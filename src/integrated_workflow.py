"""
Integrated workflow for meditation generation combining prosody, audio generation, and soundscape mixing.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, TypedDict, List
from pathlib import Path
import random
import glob

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.output_parsers import PydanticOutputParser

from src.main import (
    EmotionalState, MeditationStyle, MeditationTheme, VoiceType, SoundscapeType,
    ProsodyRequest, ProsodyAnalysis, ProsodyProfile, MeditationScript,
    PitchProfile, RateProfile, PauseProfile, EmphasisProfile
)
from audio_generator import AudioGenerator
from src.ffmpeg_mixer import process_meditation_audio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integrated_workflow')

# Constants
AUDIO_OUTPUT_DIR = "output/audio"
JSON_OUTPUT_DIR = "output/json"
SOUNDSCAPE_DIR = "soundscapes"
STATE_DIR = "output/state"

class GraphState(TypedDict):
    """The state object that will be passed between nodes in our LangGraph"""
    request: ProsodyRequest
    meditation_script: Optional[MeditationScript]
    prosody_analysis: Optional[ProsodyAnalysis]
    prosody_profile: Optional[ProsodyProfile]
    ssml_output: Optional[str]
    audio_output: Optional[Dict[str, Any]]
    error: Optional[str]
    current_step: Optional[str]

# Define workflow steps
WORKFLOW_STEPS = [
    "generate_script",
    "analyze_prosody",
    "create_profile",
    "generate_ssml",
    "generate_audio",
    "mix_audio"
]

def save_state(state: GraphState, step: str) -> str:
    """Save the current state to a JSON file"""
    os.makedirs(STATE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"state_{step}_{timestamp}.json"
    filepath = os.path.join(STATE_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
    
    return filepath

def load_state(filepath: str) -> Optional[GraphState]:
    """Load state from a JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state from {filepath}: {str(e)}")
        return None

def get_latest_state_file(step: Optional[str] = None) -> Optional[str]:
    """Get the path to the latest state file, optionally filtered by step"""
    try:
        if not os.path.exists(STATE_DIR):
            return None
            
        files = [f for f in os.listdir(STATE_DIR) if f.startswith("state_")]
        if step:
            files = [f for f in files if f.startswith(f"state_{step}_")]
            
        if not files:
            return None
            
        # Sort by timestamp in filename
        latest_file = sorted(files)[-1]
        return os.path.join(STATE_DIR, latest_file)
    except Exception as e:
        logger.error(f"Error finding latest state file: {str(e)}")
        return None

def run_workflow_step(step: str, state: Optional[GraphState] = None) -> GraphState:
    """Run a single step of the workflow"""
    if step not in WORKFLOW_STEPS:
        raise ValueError(f"Invalid step: {step}. Must be one of {WORKFLOW_STEPS}")
    
    # Load state if not provided
    if state is None:
        # Try to load the latest state from the previous step
        prev_step_idx = WORKFLOW_STEPS.index(step) - 1
        if prev_step_idx >= 0:
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            state_file = get_latest_state_file(prev_step)
            if state_file:
                state = load_state(state_file)
    
    # Initialize new state if needed
    if state is None:
        state = {
            "request": {},
            "meditation_script": None,
            "prosody_analysis": None,
            "prosody_profile": None,
            "ssml_output": None,
            "audio_output": None,
            "error": None,
            "current_step": step
        }
    
    # Create workflow graph
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("generate_script", generate_meditation_script)
    workflow.add_node("analyze_prosody", analyze_prosody_needs)
    workflow.add_node("create_profile", generate_prosody_profile)
    workflow.add_node("generate_ssml", generate_ssml)
    workflow.add_node("generate_audio", generate_meditation_audio)
    workflow.add_node("mix_audio", mix_with_soundscape)
    
    # Add edges
    for i in range(len(WORKFLOW_STEPS) - 1):
        workflow.add_edge(WORKFLOW_STEPS[i], WORKFLOW_STEPS[i + 1])
    workflow.add_edge(WORKFLOW_STEPS[-1], END)
    
    # Set entry point
    workflow.set_entry_point(step)
    
    # Compile and run
    compiled_workflow = workflow.compile()
    result = compiled_workflow.invoke(state)
    
    # Save state after step completion
    save_state(result, step)
    
    return result

def run_meditation_generation(request_data: Dict[str, Any], start_step: Optional[str] = None) -> Dict[str, Any]:
    """Run the meditation generation process, optionally starting from a specific step"""
    if start_step:
        if start_step not in WORKFLOW_STEPS:
            raise ValueError(f"Invalid start step: {start_step}. Must be one of {WORKFLOW_STEPS}")
        
        # Try to load previous state
        state = None
        prev_step_idx = WORKFLOW_STEPS.index(start_step) - 1
        if prev_step_idx >= 0:
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            state_file = get_latest_state_file(prev_step)
            if state_file:
                state = load_state(state_file)
        
        # Initialize state if needed
        if state is None:
            state = {
                "request": request_data,
                "meditation_script": None,
                "prosody_analysis": None,
                "prosody_profile": None,
                "ssml_output": None,
                "audio_output": None,
                "error": None,
                "current_step": start_step
            }
        
        return run_workflow_step(start_step, state)
    else:
        # Run complete workflow from start
        state = {
            "request": request_data,
            "meditation_script": None,
            "prosody_analysis": None,
            "prosody_profile": None,
            "ssml_output": None,
            "audio_output": None,
            "error": None,
            "current_step": WORKFLOW_STEPS[0]
        }
        return run_workflow_step(WORKFLOW_STEPS[0], state)

def generate_meditation_script(state: GraphState) -> GraphState:
    """Generate the raw meditation script based on the request parameters"""
    try:
        if "error" in state and state["error"]:
            return state

        # Initialize LLM
        llm = ChatOpenAI(temperature=0.7)
        
        # Create prompt
        system_prompt = """You are a meditation script writer. Create a meditation script that matches the requested style, theme, and emotional state.
        The script should be in the specified language and should be appropriate for the requested duration."""
        
        human_prompt = f"""Create a meditation script with the following parameters:
        - Emotional State: {state['request']['emotional_state']}
        - Meditation Style: {state['request']['meditation_style']}
        - Theme: {state['request']['meditation_theme']}
        - Duration: {state['request']['duration_minutes']} minutes
        - Language: {state['request']['language_code']}
        
        The script should be natural and flowing, with appropriate pauses and emphasis points."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        raw_response = llm.invoke(messages)
        
        # Process the script to identify sections
        script_content = raw_response.content
        script_sections = []
        
        # Simple section identification
        sections = script_content.split("\n\n")
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            section_type = "introduction" if i == 0 else "closing" if i == len(sections) - 1 else "body"
            
            # Identify special section types
            if "inhala" in section.lower() or "exhala" in section.lower() or "respira" in section.lower():
                section_type = "breathing"
            elif any(soundscape in section.lower() for soundscape in ["sonidos", "sounds", "música", "music"]):
                section_type = "soundscape"
                
            script_sections.append({
                "type": section_type,
                "content": section.strip()
            })
        
        # Create and return the updated state
        meditation_script = MeditationScript(
            content=script_content,
            sections=script_sections
        )
        
        state["meditation_script"] = meditation_script.dict()
        return state
        
    except Exception as e:
        state["error"] = f"Error generating meditation script: {str(e)}"
        return state

def analyze_prosody_needs(state: GraphState) -> GraphState:
    """Analyze the script to determine prosody needs"""
    try:
        if "error" in state and state["error"]:
            return state
            
        # Initialize LLM
        llm = ChatOpenAI(temperature=0.3)
        
        # Create parser for structured output
        parser = PydanticOutputParser(pydantic_object=ProsodyAnalysis)
        
        # Create prompts
        system_prompt = """You are a prosody analysis expert. Analyze the meditation script to determine the appropriate prosody needs."""
        
        human_prompt = f"""Analyze this meditation script for prosody needs:
        
        {state['meditation_script']['content']}
        
        Consider:
        - Overall tone needed
        - Key terms that need emphasis
        - Breathing patterns
        - Section characteristics
        """
        
        format_instructions = parser.get_format_instructions()
        
        # Generate the analysis
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt + "\n\n" + format_instructions)
        ]
        
        response = llm.invoke(messages)
        
        # Extract the structured data
        try:
            prosody_analysis = parser.parse(response.content)
            state["prosody_analysis"] = prosody_analysis.dict()
        except Exception as parsing_error:
            # Fallback parsing if the structured format fails
            analysis = {
                "overall_tone": "calming and soothing",
                "key_terms": ["respiración", "atención", "presente", "tranquilidad"],
                "breathing_patterns": [{"type": "inhale", "duration": "3s"}, {"type": "exhale", "duration": "4s"}],
                "recommended_emphasis_points": [],
                "section_characteristics": {
                    "introduction": "welcoming and grounding",
                    "body": "guiding and supportive",
                    "closing": "gentle transition to awareness"
                }
            }
            state["prosody_analysis"] = analysis
            state["parsing_warning"] = f"Could not parse structured output: {str(parsing_error)}"
            
        return state
        
    except Exception as e:
        state["error"] = f"Error analyzing prosody needs: {str(e)}"
        return state

def generate_prosody_profile(state: GraphState) -> GraphState:
    """Generate a complete prosody profile based on the analysis and request"""
    try:
        if "error" in state and state["error"]:
            return state
            
        request = state["request"]
        analysis = state["prosody_analysis"]
        
        # Map emotional states to base prosody profiles
        emotional_state = request["emotional_state"]
        
        # Create profile based on emotional state
        if emotional_state == EmotionalState.ANXIOUS.value:
            profile = ProsodyProfile(
                pitch=PitchProfile(
                    base_pitch="-10%",
                    range="moderate",
                    contour_pattern="gradual downward drift with gentle rises"
                ),
                rate=RateProfile(
                    base_rate="85%",
                    variation="moderate",
                    special_sections={
                        "breathing": "70%",
                        "introduction": "80%",
                        "closing": "75%"
                    }
                ),
                pauses=PauseProfile(
                    short_pause="800ms",
                    medium_pause="2s",
                    long_pause="4s",
                    breath_pause="3s",
                    sentence_pattern="medium after statements, long after guidance"
                ),
                emphasis=EmphasisProfile(
                    intensity="moderate",
                    key_terms=analysis["key_terms"]
                ),
                volume="soft",
                voice_quality="breathy",
                intro_adjustments={
                    "pitch": "-15%",
                    "rate": "80%"
                },
                body_adjustments={
                    "pitch": "-10%",
                    "rate": "85%"
                },
                closing_adjustments={
                    "pitch": "-15%",
                    "rate": "75%"
                },
                language_adjustments={
                    "es-ES": {
                        "rate": "80%",
                        "pitch": "-12%"
                    },
                    "en-US": {
                        "rate": "85%",
                        "pitch": "-10%"
                    }
                }
            )
        else:
            # Default profile for other emotional states
            profile = ProsodyProfile(
                pitch=PitchProfile(
                    base_pitch="-5%",
                    range="moderate",
                    contour_pattern="natural with moderate variation"
                ),
                rate=RateProfile(
                    base_rate="90%",
                    variation="moderate",
                    special_sections={
                        "breathing": "80%",
                        "introduction": "85%",
                        "closing": "85%"
                    }
                ),
                pauses=PauseProfile(
                    short_pause="500ms",
                    medium_pause="1.5s",
                    long_pause="3s",
                    breath_pause="2.5s",
                    sentence_pattern="standard"
                ),
                emphasis=EmphasisProfile(
                    intensity="moderate",
                    key_terms=analysis["key_terms"]
                ),
                volume="medium",
                voice_quality="clear",
                intro_adjustments={
                    "pitch": "-5%",
                    "rate": "85%"
                },
                body_adjustments={
                    "pitch": "-5%",
                    "rate": "90%"
                },
                closing_adjustments={
                    "pitch": "-10%",
                    "rate": "85%"
                },
                language_adjustments={
                    "es-ES": {
                        "rate": "85%",
                        "pitch": "-8%"
                    },
                    "en-US": {
                        "rate": "90%",
                        "pitch": "-5%"
                    }
                }
            )
        
        state["prosody_profile"] = profile.dict()
        return state
        
    except Exception as e:
        state["error"] = f"Error generating prosody profile: {str(e)}"
        return state

def generate_ssml(state: GraphState) -> GraphState:
    """Generate the final SSML with all prosody markup"""
    try:
        if "error" in state and state["error"]:
            return state
            
        script = state["meditation_script"]
        profile = state["prosody_profile"]
        
        # Start building the SSML
        ssml = "<speak>\n"
        
        # Process each section with appropriate prosody
        for section in script["sections"]:
            section_type = section["type"]
            content = section["content"]
            
            # Get the appropriate profile for this section
            if section_type == "introduction":
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"],
                    "rate": profile["rate"]["special_sections"]["introduction"],
                    "volume": profile["volume"]
                }
            elif section_type == "closing":
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"],
                    "rate": profile["rate"]["special_sections"]["closing"],
                    "volume": profile["volume"]
                }
            elif section_type == "breathing":
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"],
                    "rate": profile["rate"]["special_sections"]["breathing"],
                    "volume": profile["volume"]
                }
            else:  # body or other
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"],
                    "rate": profile["rate"]["base_rate"],
                    "volume": profile["volume"]
                }
            
            # Add the section with prosody
            ssml += f'<prosody rate="{section_profile["rate"]}" pitch="{section_profile["pitch"]}" volume="{section_profile["volume"]}">\n'
            
            # Process the content
            # Split into sentences
            sentences = content.split(". ")
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                processed_sentence = sentence.strip()
                
                # Add emphasis for key terms
                for term in profile["emphasis"]["key_terms"]:
                    if term.lower() in processed_sentence.lower():
                        processed_sentence = processed_sentence.replace(
                            term, 
                            f'<emphasis level="{profile["emphasis"]["intensity"]}">{term}</emphasis>'
                        )
                
                # Add the sentence to SSML
                ssml += processed_sentence + ". "
                
                # Add appropriate pause based on context
                if "inhala" in sentence.lower() or "exhala" in sentence.lower():
                    ssml += f' <break time="{profile["pauses"]["breath_pause"]}"/>\n'
                elif sentence.endswith("?"):
                    ssml += f' <break time="{profile["pauses"]["medium_pause"]}"/>\n'
                else:
                    ssml += f' <break time="{profile["pauses"]["short_pause"]}"/>\n'
            
            ssml += "</prosody>\n"
        
        ssml += "</speak>"
        
        state["ssml_output"] = ssml
        return state
        
    except Exception as e:
        state["error"] = f"Error generating SSML: {str(e)}"
        return state

def generate_meditation_audio(state: GraphState) -> GraphState:
    """Generate audio from SSML using AWS Polly"""
    try:
        if "error" in state and state["error"]:
            return state
            
        # Initialize AudioGenerator
        generator = AudioGenerator(
            aws_profile=os.environ.get('AWS_PROFILE'),
            aws_region=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            output_dir=AUDIO_OUTPUT_DIR
        )
        
        # Get the voice type and language code from the request
        voice_type_str = state["request"]["voice_type"]
        language_code = state["request"]["language_code"]
        
        # Map voice type string to enum
        voice_type_map = {
            'Male': VoiceType.MALE,
            'Female': VoiceType.FEMALE,
            'Neutral': VoiceType.NEUTRAL
        }
        voice_type = voice_type_map.get(voice_type_str, VoiceType.NEUTRAL)
        
        # Get the appropriate voice ID from the voice maps
        voice_map = generator.VOICE_MAPS.get(language_code, generator.VOICE_MAPS['en-US'])
        voice_id = voice_map.get(voice_type.value, voice_map[VoiceType.NEUTRAL.value])  # Use .value to get string
        
        # Generate audio from SSML
        audio_file = generator.generate_audio_from_ssml(
            ssml_text=state["ssml_output"],
            voice_id=voice_id,
            language_code=language_code
        )
        
        if audio_file:
            state["audio_output"] = {
                "voice_file": audio_file,
                "status": "generated"
            }
        else:
            state["error"] = "Failed to generate audio"
            
        return state
        
    except Exception as e:
        state["error"] = f"Error generating audio: {str(e)}"
        return state

def find_background_file(soundscape_dir: str, soundscape_type: str) -> Optional[str]:
    """Find a background soundscape file matching the type, or pick a random one."""
    # Try to find files matching the type
    pattern = os.path.join(soundscape_dir, f"*{soundscape_type.lower()}*.mp3")
    matches = glob.glob(pattern)
    if matches:
        return random.choice(matches)
    # Fallback: pick any mp3 in the directory
    all_files = glob.glob(os.path.join(soundscape_dir, "*.mp3"))
    if all_files:
        return random.choice(all_files)
    return None

def mix_with_soundscape(state: GraphState) -> GraphState:
    """Mix generated audio with background soundscape using ffmpeg mixer"""
    try:
        if "error" in state and state["error"]:
            return state
        
        if not state.get("audio_output", {}).get("voice_file"):
            state["error"] = "No voice file to mix"
            return state
        
        # Find a background soundscape file
        soundscape_type = state["request"].get("soundscape", "nature")
        background_file = find_background_file(SOUNDSCAPE_DIR, soundscape_type)
        if not background_file:
            state["error"] = f"No suitable soundscape file found for type: {soundscape_type}"
            return state
        
        # Process audio with ffmpeg mixer
        full_audio, sample_audio = process_meditation_audio(
            voice_file=state["audio_output"]["voice_file"],
            background_file=background_file,
            output_dir=AUDIO_OUTPUT_DIR,
            background_volume=0.3,
            create_sample=True
        )
        
        if full_audio:
            state["audio_output"].update({
                "full_audio": full_audio,
                "sample_audio": sample_audio,
                "status": "completed"
            })
            
            # Save the complete state to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_output = {
                "request": state["request"],
                "meditation_script": state["meditation_script"],
                "prosody_analysis": state["prosody_analysis"],
                "prosody_profile": state["prosody_profile"],
                "audio_output": state["audio_output"]
            }
            
            json_file = os.path.join(JSON_OUTPUT_DIR, f"meditation_{timestamp}.json")
            os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
            
            with open(json_file, 'w') as f:
                json.dump(json_output, f, indent=2)
                
            state["audio_output"]["json_file"] = json_file
        else:
            state["error"] = "Failed to mix audio with soundscape (ffmpeg)"
            
        return state
        
    except Exception as e:
        state["error"] = f"Error mixing audio (ffmpeg): {str(e)}"
        return state 