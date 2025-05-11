"""
Integrated workflow for meditation generation combining prosody, audio generation, and soundscape mixing.
This file combines the functionality of the original main.py and integrated_workflow.py.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional, Any, TypedDict, List, Union
from pathlib import Path
import random
import glob
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.output_parsers import PydanticOutputParser

# Fix import paths
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audio_generator import AudioGenerator
from src.ffmpeg_mixer import process_meditation_audio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("meditation_workflow.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('integrated_workflow')

# Constants
AUDIO_OUTPUT_DIR = "output/audio"
JSON_OUTPUT_DIR = "output/json"
SOUNDSCAPE_DIR = "soundscapes"
STATE_DIR = "output/state"

# ============ Data Models ============

class EmotionalState(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    CALM = "calm"
    STRESSED = "stressed"
    TIRED = "tired"
    ENERGETIC = "energetic"
    NEUTRAL = "neutral"

class MeditationStyle(str, Enum):
    MINDFULNESS = "Mindfulness"
    GUIDED_IMAGERY = "GuidedImagery"
    BODY_SCAN = "BodyScan"
    LOVING_KINDNESS = "LovingKindness"
    BREATH_FOCUS = "BreathFocus"
    PROGRESSIVE_RELAXATION = "ProgressiveRelaxation"

class MeditationTheme(str, Enum):
    STRESS_RELIEF = "StressRelief"
    SLEEP = "Sleep"
    FOCUS = "Focus"
    SELF_COMPASSION = "SelfCompassion"
    ANXIETY_RELIEF = "AnxietyRelief"
    CONFIDENCE = "Confidence"
    GRATITUDE = "Gratitude"

class VoiceType(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"

class SoundscapeType(str, Enum):
    NATURE = "Nature"
    URBAN = "Urban"
    AMBIENT = "Ambient"
    SILENCE = "Silence"
    RAIN = "Rain"
    OCEAN = "Ocean"
    FOREST = "Forest"
    NIGHTTIME = "Nighttime"

# ============ Advanced Prosody Models ============

class PitchProfile(BaseModel):
    base_pitch: str = Field(description="Base pitch adjustment, e.g. '-10%', 'low'")
    range: str = Field(description="Pitch range/variation, e.g. '+20%', 'wide'")
    contour_pattern: str = Field(description="Natural pitch contour description")
    emotional_contours: Dict[str, str] = Field(
        description="Pitch contours for different emotional states",
        default_factory=lambda: {
            "calm": "gradual downward drift with gentle rises",
            "anxious": "higher baseline with more variation",
            "energetic": "higher baseline with upward contours",
            "tired": "lower baseline with minimal variation",
            "happy": "moderate baseline with upward contours",
            "sad": "lower baseline with downward contours",
            "stressed": "higher baseline with tense contours"
        }
    )

class RateProfile(BaseModel):
    base_rate: str = Field(description="Base speaking rate, e.g. '90%', 'slow'")
    variation: str = Field(description="Rate variation pattern")
    special_sections: Dict[str, str] = Field(
        description="Rate adjustments for special sections",
        default_factory=lambda: {
            "breathing": "70%",
            "introduction": "80%",
            "closing": "75%",
            "grounding": "65%",
            "body_scan": "60%",
            "affirmations": "75%",
            "visualization": "70%"
        }
    )
    emotional_rates: Dict[str, str] = Field(
        description="Rate adjustments for different emotional states",
        default_factory=lambda: {
            "calm": "70%",
            "anxious": "85%",
            "energetic": "90%",
            "tired": "65%",
            "happy": "85%",
            "sad": "70%",
            "stressed": "80%"
        }
    )

class PauseProfile(BaseModel):
    short_pause: str = Field(description="Duration for short pauses, e.g. '500ms'")
    medium_pause: str = Field(description="Duration for medium pauses, e.g. '1s'")
    long_pause: str = Field(description="Duration for long pauses, e.g. '3s'")
    breath_pause: str = Field(description="Duration for breathing instruction pauses, e.g. '4s'")
    sentence_pattern: str = Field(description="Pattern for sentence pauses")
    breathing_patterns: Dict[str, Dict[str, str]] = Field(
        description="Pause patterns for different breathing techniques",
        default_factory=lambda: {
            "4-7-8": {
                "inhale": "4s",
                "hold": "7s",
                "exhale": "8s"
            },
            "box_breathing": {
                "inhale": "4s",
                "hold_in": "4s",
                "exhale": "4s",
                "hold_out": "4s"
            },
            "deep_breathing": {
                "inhale": "4s",
                "exhale": "6s"
            }
        }
    )

class EmphasisProfile(BaseModel):
    intensity: str = Field(description="Overall emphasis intensity")
    key_terms: List[str] = Field(description="Terms to emphasize")
    emotional_emphasis: Dict[str, str] = Field(
        description="Emphasis patterns for different emotional states",
        default_factory=lambda: {
            "calm": "reduced",
            "anxious": "moderate",
            "energetic": "strong",
            "tired": "reduced",
            "happy": "moderate",
            "sad": "reduced",
            "stressed": "moderate"
        }
    )

class ProsodyProfile(BaseModel):
    """Complete prosody profile for a specific emotional state and meditation context"""
    pitch: PitchProfile
    rate: RateProfile
    pauses: PauseProfile
    emphasis: EmphasisProfile
    volume: str = Field(description="Overall volume setting, e.g. 'soft', 'medium', '+5dB'")
    voice_quality: Optional[str] = Field(default=None, description="Voice quality hint if supported")
    
    # Section-specific profiles
    section_profiles: Dict[str, Dict[str, str]] = Field(
        description="Detailed profiles for different section types",
        default_factory=lambda: {
            "introduction": {
                "pitch": "-15%",
                "rate": "80%",
                "volume": "soft"
            },
            "grounding": {
                "pitch": "-20%",
                "rate": "65%",
                "volume": "x-soft"
            },
            "body_scan": {
                "pitch": "-18%",
                "rate": "60%",
                "volume": "x-soft"
            },
            "breathing": {
                "pitch": "-15%",
                "rate": "70%",
                "volume": "soft"
            },
            "visualization": {
                "pitch": "-12%",
                "rate": "75%",
                "volume": "soft"
            },
            "affirmations": {
                "pitch": "-10%",
                "rate": "75%",
                "volume": "medium"
            },
            "closing": {
                "pitch": "-15%",
                "rate": "75%",
                "volume": "soft"
            }
        }
    )
    
    # Language-specific adjustments
    language_adjustments: Dict[str, Dict[str, str]] = Field(
        description="Adjustments specific to each language code",
        default_factory=lambda: {
            "es-ES": {
                "rate": "80%",
                "pitch": "-12%",
                "volume": "soft"
            },
            "en-US": {
                "rate": "85%",
                "pitch": "-10%",
                "volume": "medium"
            }
        }
    )
    
    # Progressive changes throughout the meditation
    progression: Dict[str, Dict[str, str]] = Field(
        description="How prosody changes throughout the meditation",
        default_factory=lambda: {
            "start": {
                "rate": "85%",
                "pitch": "-10%",
                "volume": "medium"
            },
            "middle": {
                "rate": "75%",
                "pitch": "-15%",
                "volume": "soft"
            },
            "end": {
                "rate": "70%",
                "pitch": "-20%",
                "volume": "x-soft"
            }
        }
    )

class ProsodyRequest(BaseModel):
    """Input request for the prosody system"""
    emotional_state: EmotionalState
    meditation_style: MeditationStyle
    meditation_theme: MeditationTheme
    duration_minutes: int
    voice_type: VoiceType
    language_code: str
    soundscape: SoundscapeType

class MeditationScript(BaseModel):
    """Raw meditation script text"""
    content: str
    sections: List[Dict[str, str]] = Field(
        description="Identified sections of the meditation (intro, body, guidance, closing, etc.)"
    )

class ProsodyAnalysis(BaseModel):
    """Analysis of prosody needs for the specific meditation"""
    overall_tone: str
    key_terms: List[str]
    breathing_patterns: List[Dict[str, str]]
    recommended_emphasis_points: List[Dict[str, str]]
    section_characteristics: Dict[str, str]

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
    "review_and_improve_ssml",  # Add the new step
    "generate_audio",
    "mix_audio"
]

# ============ Helper Functions ============

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
            logger.warning(f"State directory does not exist: {STATE_DIR}")
            return None
            
        logger.info(f"Looking for latest state file{f' for step {step}' if step else ''}")
        
        # List all state files
        all_files = [f for f in os.listdir(STATE_DIR) if f.startswith("state_")]
        logger.info(f"Found {len(all_files)} total state files")
        
        if not all_files:
            logger.warning("No state files found")
            return None
            
        # Filter by step if requested
        if step:
            # Match the exact step (state_step_timestamp.json format)
            matching_files = [f for f in all_files if f.startswith(f"state_{step}_")]
            if not matching_files:
                logger.warning(f"No state files found for step: {step}")
                return None
                
            logger.info(f"Found {len(matching_files)} state files for step {step}")
            
            # Sort by timestamp in filename (most recent last)
            latest_file = sorted(matching_files)[-1]
            logger.info(f"Latest state file for step {step}: {latest_file}")
            return os.path.join(STATE_DIR, latest_file)
        else:
            # Get all steps in order
            step_prefixes = [f"state_{s}_" for s in WORKFLOW_STEPS]
            
            # Find the latest file for each step
            latest_step_files = []
            for prefix in step_prefixes:
                matching_files = [f for f in all_files if f.startswith(prefix)]
                if matching_files:
                    latest_step_files.append(sorted(matching_files)[-1])
            
            if not latest_step_files:
                logger.warning("No matching state files found")
                return None
                
            # Sort by step order in workflow
            latest_file = sorted(latest_step_files, 
                                key=lambda f: WORKFLOW_STEPS.index(f.split('_')[1]))[-1]
            
            logger.info(f"Latest overall state file: {latest_file}")
            return os.path.join(STATE_DIR, latest_file)
            
    except Exception as e:
        logger.error(f"Error finding latest state file: {str(e)}")
        return None

def split_into_sentences(text):
    """Simple sentence splitter - would be more sophisticated in production"""
    import re
    # Split on periods, question marks, and exclamation points
    # but keep the punctuation with the sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty sentences
    return [s for s in sentences if s.strip()]

# ============ Workflow Node Functions ============

def log_state_transition(current_step: str, state: GraphState) -> None:
    """Log detailed information about the current state of the workflow"""
    logger.info(f"===== STEP: {current_step} =====")
    
    # Log only the essential state information without huge content
    state_log = {}
    for key, value in state.items():
        if key == "meditation_script" and value:
            state_log[key] = {"length": len(value.get("content", "")), "sections": len(value.get("sections", []))}
        elif key == "prosody_analysis" and value:
            state_log[key] = {"overall_tone": value.get("overall_tone", ""), "key_terms_count": len(value.get("key_terms", []))}
        elif key == "prosody_profile" and value:
            state_log[key] = {"base_rate": value.get("rate", {}).get("base_rate", "") if isinstance(value.get("rate"), dict) else ""}
        elif key == "ssml_output" and value:
            state_log[key] = {"length": len(value), "has_speak_tag": "<speak>" in value and "</speak>" in value}
        elif key == "audio_output" and value:
            state_log[key] = {"status": value.get("status", ""), "voice_file": value.get("voice_file", "")}
        else:
            state_log[key] = value
    
    logger.info(f"State summary: {json.dumps(state_log, indent=2)}")

def log_llm_interaction(prompt: str, response_content: str, model: str, purpose: str) -> None:
    """Log details of an LLM interaction"""
    logger.info(f"LLM Interaction: {purpose}")
    logger.info(f"Model: {model}")
    
    # Log truncated versions of prompt and response
    prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
    response_preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
    
    logger.info(f"Prompt preview: {prompt_preview}")
    logger.info(f"Response preview: {response_preview}")
    
    # Also log the full interaction to a separate file for detailed analysis
    detailed_log_path = f"logs/llm_interactions/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{purpose.replace(' ', '_')}.json"
    os.makedirs(os.path.dirname(detailed_log_path), exist_ok=True)
    
    with open(detailed_log_path, 'w') as f:
        json.dump({
            "purpose": purpose,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response_content
        }, f, indent=2)
    
    logger.info(f"Detailed log saved to: {detailed_log_path}")

def generate_meditation_script(state: GraphState) -> GraphState:
    """Generate a detailed meditation script with LLM including section identification"""
    try:
        logger.info("Starting meditation script generation")
        log_state_transition("generate_meditation_script", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state

        # Initialize LLM with higher temperature for more creative script generation
        llm = ChatOpenAI(temperature=0.7, model="gpt-4o")
        
        # Create a detailed system prompt with meditation expertise
        system_prompt = """You are an expert meditation script writer with a background in mindfulness, psychology, and therapeutic communication.

Your task is to create a guided meditation script that is highly effective, engaging, and tailored to specific needs. Each script should include:

1. A welcoming introduction that establishes the intention and creates a safe space
2. An initial grounding section to help the listener settle in and become present
3. Breathing guidance with appropriate pacing and instructions
4. The main practice section, which varies based on the meditation style:
   - For mindfulness: attention anchoring, present moment awareness
   - For body scan: progressive attention to body parts with relaxation cues
   - For loving-kindness: compassion cultivation with specific phrases
   - For guided imagery: vivid and immersive sensory descriptions
   - For breath focus: rhythmic breathing patterns with counting or visualization
   - For progressive relaxation: systematic muscle relaxation sequences

5. Appropriate transitional phrases between sections
6. A gentle closing that integrates the practice and prepares for return to regular activities

Your language should be:
- Clear and accessible without being simplistic
- Inclusive and non-judgmental
- Paced appropriately for the requested duration
- Culturally appropriate for the specified language

Explicitly mark each section with its type (e.g., [INTRODUCTION], [BODY_SCAN], [BREATHING], [CLOSING]) to aid in prosody processing."""

        # Create a detailed human prompt with all context
        human_prompt = f"""Create a {state["request"]["duration_minutes"]}-minute {state["request"]["meditation_style"]} meditation script focused on {state["request"]["meditation_theme"]} for someone feeling {state["request"]["emotional_state"]}.

The script should be in {state["request"]["language_code"]} and voiced by a {state["request"]["voice_type"]} voice.

Include these essential components:
1. A welcoming introduction (30-45 seconds)
2. Grounding/centering instructions
3. Breathing guidance appropriate for this style and emotional state
4. The main practice section specific to {state["request"]["meditation_style"]}
5. A gentle closing with integration (30-45 seconds)

Structure the script clearly with section markers like [INTRODUCTION], [BREATHING], [BODY_SCAN], etc., to enable appropriate prosody processing.

Timing guidance:
- For a {state["request"]["duration_minutes"]}-minute meditation, the script should be approximately {state["request"]["duration_minutes"] * 125} words
- Allow for natural pauses and breathing spaces
- Pace the script to avoid rushing while maintaining engagement

Remember that this script will be processed with SSML for voice synthesis, so maintain a natural speaking rhythm."""

        # Generate the script
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        logger.info(f"Requesting script generation for {state['request']['meditation_style']} meditation on {state['request']['meditation_theme']}")
        response = llm.invoke(messages)
        script_content = response.content
        
        # Log the LLM interaction
        log_llm_interaction(
            prompt=human_prompt,
            response_content=script_content,
            model=llm.model_name,
            purpose="Meditation Script Generation"
        )
        
        logger.info(f"Generated script with {len(script_content)} characters")
        
        # Use LLM to analyze script sections rather than simple text splitting
        section_analysis_prompt = f"""Analyze this meditation script and identify distinct sections with their boundaries.

SCRIPT:
{script_content}

For each section, determine:
1. The section type (introduction, grounding, breathing, body_scan, visualization, affirmation, closing, etc.)
2. The start and end of each section (by paragraph number or first few words)
3. The primary function of that section in the meditation

Return the analysis as a JSON structure with each section containing the section type, content, and function."""

        # Get detailed section analysis
        logger.info("Requesting section analysis")
        section_analysis_response = llm.invoke([HumanMessage(content=section_analysis_prompt)])
        
        # Log the section analysis interaction
        log_llm_interaction(
            prompt=section_analysis_prompt,
            response_content=section_analysis_response.content,
            model=llm.model_name,
            purpose="Script Section Analysis"
        )
        
        # Extract sections and create structured script
        try:
            # Try to parse JSON from the section analysis
            import json
            import re
            
            # Look for JSON content in the response
            json_match = re.search(r'({.*}|\[.*\])', section_analysis_response.content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0).strip()
            else:
                # Try to find a JSON object directly
                json_match = re.search(r'({.+})', section_analysis_response.content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # Use LLM to fix the format
                    fix_prompt = f"""The previous section analysis couldn't be parsed as JSON. Please reformat it as a valid JSON array of section objects like this:

[
  {{
    "type": "introduction",
    "content": "Full text of this section",
    "function": "Welcome and establish intention"
  }},
  {{
    "type": "breathing",
    "content": "Full text of this section",
    "function": "Guide initial breath awareness"
  }},
  ... and so on
]

Original response:
{section_analysis_response.content}

Just return the valid JSON with no explanation."""
                    
                    fix_response = llm.invoke([HumanMessage(content=fix_prompt)])
                    fix_content = fix_response.content
                    
                    # Try to extract JSON again
                    json_match = re.search(r'({.*}|\[.*\])', fix_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0).strip()
                    else:
                        json_match = re.search(r'(\[{.+}\])', fix_content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1).strip()
                        else:
                            json_str = fix_content
            
            # Parse section data
            section_data = json.loads(json_str)
            
            # Extract sections from parsed data
            script_sections = []
            for section in section_data:
                script_sections.append({
                    "type": section["type"],
                    "content": section["content"]
                })
                
        except Exception as parsing_error:
            # Fallback manual section extraction using regex
            # Look for section markers in brackets [SECTION_NAME]
            section_markers = re.findall(r'\[(.*?)\](.*?)(?=\[|$)', script_content, re.DOTALL)
            
            if section_markers:
                script_sections = []
                for marker, content in section_markers:
                    section_type = marker.lower().strip()
                    # Map common section names to standardized types
                    if "intro" in section_type:
                        section_type = "introduction"
                    elif "breath" in section_type:
                        section_type = "breathing"
                    elif "body" in section_type and "scan" in section_type:
                        section_type = "body_scan"
                    elif "visual" in section_type:
                        section_type = "visualization"
                    elif "affirm" in section_type:
                        section_type = "affirmations"
                    elif "clos" in section_type:
                        section_type = "closing"
                    elif "ground" in section_type:
                        section_type = "grounding"
                    
                    script_sections.append({
                        "type": section_type,
                        "content": content.strip()
                    })
            else:
                # If no section markers, fall back to simple paragraph splitting
                sections = script_content.split("\n\n")
                
                script_sections = []
                for i, section in enumerate(sections):
                    if not section.strip():
                        continue
                    
                    section_type = "introduction" if i == 0 else "closing" if i == len(sections) - 1 else "body"
                    
                    # Simple heuristic detection
                    if re.search(r'(inhala|exhala|respira|breathe|inhale|exhale)', section.lower()):
                        section_type = "breathing"
                    elif re.search(r'(body|cuerpo|scan|muscles|músculos)', section.lower()):
                        section_type = "body_scan"
                    elif re.search(r'(imagine|visualize|visualiza|imagina)', section.lower()):
                        section_type = "visualization"
                    
                    script_sections.append({
                        "type": section_type,
                        "content": section.strip()
                    })
            
            state["section_parsing_error"] = f"Used fallback section parsing: {str(parsing_error)}"
        
        # Create and return the updated state
        meditation_script = MeditationScript(
            content=script_content,
            sections=script_sections
        )
        
        state["meditation_script"] = meditation_script.dict()
        logger.info(f"Completed script generation with {len(script_sections)} sections")
        log_state_transition("generate_meditation_script_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error generating meditation script: {str(e)}")
        state["error"] = f"Error generating meditation script: {str(e)}"
        return state

def analyze_prosody_needs(state: GraphState) -> GraphState:
    """Analyze the script to determine prosody needs using sophisticated LLM analysis"""
    try:
        logger.info("Starting prosody needs analysis")
        log_state_transition("analyze_prosody_needs", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        # Initialize LLM with higher temperature for more creative analysis
        llm = ChatOpenAI(temperature=0.3, model="gpt-4o")
        
        # Create a comprehensive prompt that leverages the LLM's capabilities
        system_prompt = """You are a prosody analysis expert for meditation narration with deep expertise in SSML for AWS Polly. 
        Your task is to analyze meditation scripts and provide detailed prosody recommendations.
        
        Analyze the script comprehensively, considering:
        1. Emotional undertones and progression throughout the meditation
        2. Natural speech patterns and appropriate pauses
        3. Specific breathing patterns and their timing requirements
        4. Sections that require changes in pace, pitch, or volume
        5. Words or phrases that should receive emphasis
        6. Appropriate pacing for deepening relaxation over time
        
        Consider how the script's structure affects vocal delivery:
        - Introduction sections typically need a welcoming, moderate pace
        - Grounding sections benefit from a slower, deeper voice
        - Breathing instruction sections need careful timing and clear articulation
        - Body scan sections work best with a gentle, methodical progression
        - Visualization sections require an evocative, soothing quality
        - Closing sections should provide gentle transition back to awareness
        
        For AWS Polly Neural voices, remember:
        - Emphasis tags don't work, so suggest prosody alternatives
        - Breathing sounds must be created with breaks, not auto-breaths
        - Whispered effects aren't available, so suggest volume/rate alternatives
        
        Analyze the script deeply and create a comprehensive prosody profile."""
        
        human_prompt = f"""I need a detailed prosody analysis for this meditation script that will be narrated using AWS Polly Neural voices (primarily Joanna for English, Conchita for Spanish).

Script context:
- Emotional state: {state['request']['emotional_state']}
- Meditation style: {state['request']['meditation_style']}
- Theme: {state['request']['meditation_theme']}
- Duration: {state['request']['duration_minutes']} minutes
- Language: {state['request']['language_code']}

Here is the meditation script:
        {state['meditation_script']['content']}
        
Please provide a comprehensive prosody analysis that includes:

1. Overall tone characterization
2. Section identification with boundaries and characteristics:
   - Introduction/welcome
   - Grounding
   - Body scan sections
   - Breathing instruction sections (with pattern detection)
   - Visualization sections
   - Affirmation sections
   - Closing/transition

3. Breathing pattern detection:
   - Identify specific breathing techniques (4-7-8, box breathing, etc.)
   - Recommend appropriate pause timings for each phase
   - Note where breathing guidance occurs

4. Key terms for emphasis:
   - Important words that deserve prosodic emphasis
   - Terms central to the meditation's theme
   - Repeated phrases or mantras

5. Emotional progression stages:
   - How voice quality should change from beginning to middle to end
   - Moments of heightened guidance vs. deeper relaxation

Your analysis should be detailed enough to guide SSML generation with appropriate prosody tags."""
        
        # Get detailed analysis
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        # Format instructions are specific to the required output structure
        format_instructions = """
        Your response should be a JSON object with the following structure:
        {
          "overall_tone": "description of the overall tone",
          "key_terms": ["term1", "term2", ...],
          "breathing_patterns": [
            {
              "type": "pattern name",
              "phases": {
                "inhale": "duration",
                "hold": "duration",
                "exhale": "duration"
              },
              "location": "description of where this occurs"
            }
          ],
          "section_characteristics": {
            "introduction": {
              "type": "specific type",
              "tone": "tone description",
              "boundaries": "approximate line numbers or phrases",
              "prosody": {
                "rate": "rate value",
                "pitch": "pitch value",
                "volume": "volume value"
              }
            },
            "body": { similar structure },
            "closing": { similar structure },
            ... other sections ...
          },
          "progression": {
            "start": {
              "rate": "rate value",
              "pitch": "pitch value",
              "volume": "volume value"
            },
            "middle": { similar structure },
            "end": { similar structure }
          },
          "recommended_emphasis_points": [
            {
              "phrase": "phrase to emphasize",
              "reason": "why this should be emphasized",
              "technique": "prosody adjustment recommendation"
            }
          ]
        }
        """
        
        # Generate the analysis
        logger.info("Requesting prosody analysis")
        response = llm.invoke(messages + [HumanMessage(content=format_instructions)])
        
        # Log the prosody analysis interaction
        log_llm_interaction(
            prompt=human_prompt + "\n\n" + format_instructions,
            response_content=response.content,
            model=llm.model_name,
            purpose="Prosody Analysis"
        )
        
        # Extract the structured data
        try:
            # Try to parse JSON from the response
            import json
            import re
            
            # Extract JSON content from the response
            content = response.content
            # Look for JSON content in the response
            json_match = re.search(r'({.*}|\[.*\])', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0).strip()
            else:
                # Try to find a JSON object directly
                json_match = re.search(r'({.+})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # Assume the entire content is JSON
                    json_str = content
            
            # Parse the JSON string
            prosody_analysis = json.loads(json_str)
            state["prosody_analysis"] = prosody_analysis
            
        except Exception as parsing_error:
            # Create a more intelligent fallback by asking the LLM to fix the format
            fallback_prompt = f"""I received the following analysis, but it's not in the correct JSON format. 
            Please reformat it according to the required structure:
            
            {response.content}
            
            Required format:
            {format_instructions}
            
            Just return the properly formatted JSON with no explanation."""
            
            try:
                fallback_response = llm.invoke([HumanMessage(content=fallback_prompt)])
                fallback_content = fallback_response.content
                
                # Try to extract and parse JSON again
                json_match = re.search(r'({.*}|\[.*\])', fallback_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0).strip()
                else:
                    json_match = re.search(r'({.+})', fallback_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    else:
                        json_str = fallback_content
                
                prosody_analysis = json.loads(json_str)
                state["prosody_analysis"] = prosody_analysis
                state["parsing_warning"] = f"Used fallback parsing: {str(parsing_error)}"
                
            except Exception as fallback_error:
                # If all else fails, create a basic analysis structure
                state["prosody_analysis"] = {
                "overall_tone": "calming and soothing",
                    "key_terms": ["breath", "relax", "present", "awareness", "gentle"],
                    "breathing_patterns": [
                        {
                            "type": "deep_breathing",
                            "phases": {
                                "inhale": "4s",
                                "exhale": "6s"
                            }
                        }
                    ],
                "section_characteristics": {
                        "introduction": {
                            "type": "grounding",
                            "tone": "welcoming and grounding",
                            "prosody": {
                                "rate": "80%",
                                "pitch": "-15%",
                                "volume": "soft"
                            }
                        },
                        "body": {
                            "type": "guidance",
                            "tone": "supportive and gentle",
                            "prosody": {
                                "rate": "70%",
                                "pitch": "-18%",
                                "volume": "x-soft"
                            }
                        },
                        "closing": {
                            "type": "transition",
                            "tone": "gentle transition to awareness",
                            "prosody": {
                                "rate": "75%",
                                "pitch": "-15%",
                                "volume": "soft"
                            }
                        }
                    },
                    "progression": {
                        "start": {
                            "rate": "85%",
                            "pitch": "-10%",
                            "volume": "medium"
                        },
                        "middle": {
                            "rate": "75%",
                            "pitch": "-15%",
                            "volume": "soft"
                        },
                        "end": {
                            "rate": "70%",
                            "pitch": "-20%",
                            "volume": "x-soft"
                        }
                    },
                    "recommended_emphasis_points": []
                }
                state["parsing_error"] = f"Could not parse response: {str(parsing_error)} → {str(fallback_error)}"
            
        logger.info("Completed prosody analysis")
        log_state_transition("analyze_prosody_needs_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error analyzing prosody needs: {str(e)}")
        state["error"] = f"Error analyzing prosody needs: {str(e)}"
        return state

def generate_prosody_profile(state: GraphState) -> GraphState:
    """Generate a comprehensive prosody profile using LLM to consider all contextual factors"""
    try:
        logger.info("Starting prosody profile generation")
        log_state_transition("generate_prosody_profile", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        request = state["request"]
        analysis = state["prosody_analysis"]
        import json  # Add json import here
        
        # First approach: Use LLM to generate the complete prosody profile
        llm = ChatOpenAI(temperature=0.3, model="gpt-4o")
        
        system_prompt = """You are an expert in speech prosody for meditation, with deep knowledge of AWS Polly's SSML capabilities and Neural voices.

Your task is to create a comprehensive prosody profile that will guide SSML generation for a meditation narration.

Consider these key aspects:
1. The emotional state and meditation style determine the overall prosody approach
2. Different sections (introduction, body scan, breathing) need specialized prosody settings
3. AWS Polly Neural voices support specific SSML tags and have specific optimal ranges
4. A meditation should have progressive prosody changes to deepen relaxation over time
5. Language-specific considerations affect optimal pitch, rate, and volume settings

Your profile should include precise values for:
- Pitch settings (base pitch, range, contours)
- Rate settings (overall pace, variations for different sections)
- Pause durations (short, medium, long, breath-specific)
- Volume settings (overall and section-specific)
- Section-specific profiles (intro, body scan, breathing, closing, etc.)
- Progressive changes throughout the meditation

Use percentage values for rate/pitch (e.g., "80%", "-15%") and specific time values for pauses (e.g., "800ms", "2s").
Remember that Neural voices cannot use emphasis tags, so adjust pitch/rate/volume instead."""

        human_prompt = f"""Create a comprehensive prosody profile for this meditation:

CONTEXT:
- Emotional state: {request['emotional_state']}
- Meditation style: {request['meditation_style']}
- Theme: {request['meditation_theme']}
- Duration: {request['duration_minutes']} minutes
- Language: {request['language_code']}
- Voice: {request['voice_type']} ({request['language_code']})

PROSODY ANALYSIS:
{json.dumps(analysis, indent=2)}

The prosody profile should include:

1. PitchProfile:
   - base_pitch: Base pitch adjustment
   - range: Pitch range/variation
   - contour_pattern: Natural pitch contour description
   - emotional_contours: Pitch patterns for different emotional states

2. RateProfile:
   - base_rate: Base speaking rate
   - variation: Rate variation pattern
   - special_sections: Rate adjustments for different sections
   - emotional_rates: Rate adjustments for different emotional states

3. PauseProfile:
   - short_pause: Duration for short pauses
   - medium_pause: Duration for medium pauses
   - long_pause: Duration for long pauses
   - breath_pause: Duration for breathing instruction pauses
   - sentence_pattern: Pattern for sentence pauses
   - breathing_patterns: Pause durations for different breathing techniques

4. EmphasisProfile:
   - intensity: Overall emphasis intensity (but implemented with prosody)
   - key_terms: Terms to emphasize
   - emotional_emphasis: Emphasis patterns for different states

5. Section profiles for different meditation parts
6. Language-specific adjustments
7. Progressive changes throughout the meditation

Return a complete prosody profile optimized for AWS Polly Neural voices and the specific meditation context."""

        format_instructions = """
Your response should be a JSON object representing a complete ProsodyProfile. Here's the expected format:

{
  "pitch": {{ "base_pitch": "-10%", "range": "moderate", "contour_pattern": "gradual downward drift with gentle rises", "emotional_contours": {{ "calm": "gradual downward drift with gentle rises", "anxious": "higher baseline with more variation", "energetic": "higher baseline with upward contours", "tired": "lower baseline with minimal variation", "happy": "moderate baseline with upward contours", "sad": "lower baseline with downward contours", "stressed": "higher baseline with tense contours" }} }},
  "rate": {{ "base_rate": "85%", "variation": "moderate", "special_sections": {{ "breathing": "70%", "introduction": "80%", "closing": "75%", "grounding": "65%", "body_scan": "60%", "affirmations": "75%", "visualization": "70%" }}, "emotional_rates": {{ "calm": "70%", "anxious": "85%", "energetic": "90%", "tired": "65%", "happy": "85%", "sad": "70%", "stressed": "80%" }} }},
  "pauses": {{ "short_pause": "800ms", "medium_pause": "2s", "long_pause": "4s", "breath_pause": "3s", "sentence_pattern": "medium after statements, long after guidance", "breathing_patterns": {{ "4-7-8": {{ "inhale": "4s", "hold": "7s", "exhale": "8s" }}, "box_breathing": {{ "inhale": "4s", "hold_in": "4s", "exhale": "4s", "hold_out": "4s" }}, "deep_breathing": {{ "inhale": "4s", "exhale": "6s" }} }}, "emphasis": {{ "intensity": "moderate", "key_terms": ["awareness", "breath", "present"], "emotional_emphasis": {{ "calm": "reduced", "anxious": "moderate", "energetic": "strong", "tired": "reduced", "happy": "moderate", "sad": "reduced", "stressed": "moderate" }} }}, "volume": "soft", "voice_quality": "breathy", "section_profiles": {{ "introduction": {{ "pitch": "-15%", "rate": "80%", "volume": "soft" }}, "grounding": {{ "pitch": "-20%", "rate": "65%", "volume": "x-soft" }}, "body_scan": {{ "pitch": "-18%", "rate": "60%", "volume": "x-soft" }}, "breathing": {{ "pitch": "-15%", "rate": "70%", "volume": "soft" }}, "visualization": {{ "pitch": "-12%", "rate": "75%", "volume": "soft" }}, "affirmations": {{ "pitch": "-10%", "rate": "75%", "volume": "medium" }}, "closing": {{ "pitch": "-15%", "rate": "75%", "volume": "soft" }} }}, "language_adjustments": {{ "es-ES": {{ "rate": "80%", "pitch": "-12%", "volume": "soft" }}, "en-US": {{ "rate": "85%", "pitch": "-10%", "volume": "medium" }} }}, "progression": {{ "start": {{ "rate": "85%", "pitch": "-10%", "volume": "medium" }}, "middle": {{ "rate": "75%", "pitch": "-15%", "volume": "soft" }}, "end": {{ "rate": "70%", "pitch": "-20%", "volume": "x-soft" }} }}
}}
"""

        # Generate the profile
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
            HumanMessage(content=format_instructions)
        ]
        
        logger.info("Requesting prosody profile generation")
        response = llm.invoke(messages)
        
        # Log the prosody profile interaction
        log_llm_interaction(
            prompt=human_prompt + "\n\n" + format_instructions,
            response_content=response.content,
            model=llm.model_name,
            purpose="Prosody Profile Generation"
        )
        
        # Extract and parse the profile
        try:
            # Try to parse JSON from the response
            import json
            import re
            
            # Extract JSON content from the response
            content = response.content
            # Look for JSON content in the response
            json_match = re.search(r'({.*}|\[.*\])', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0).strip()
            else:
                # Try to find a JSON object directly
                json_match = re.search(r'({.+})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # Assume the entire content is JSON
                    json_str = content
            
            # Parse the JSON string
            prosody_profile = json.loads(json_str)
            state["prosody_profile"] = prosody_profile
            
        except Exception as parsing_error:
            # Fallback approach: create a profile based on emotional state and analysis
            try:
                # Request a simpler format
                fix_prompt = f"""The previous response couldn't be parsed as JSON. Please provide the prosody profile as valid JSON with no additional text or explanation. Use the following simplified structure:

{{
  "pitch": {{ "base_pitch": "-10%", "range": "moderate", "contour_pattern": "description" }},
  "rate": {{ "base_rate": "85%", "variation": "moderate", "special_sections": {{ "breathing": "70%" }} }},
  "pauses": {{ "short_pause": "800ms", "medium_pause": "2s", "long_pause": "4s", "breath_pause": "3s" }},
  "emphasis": {{ "intensity": "moderate", "key_terms": ["term1", "term2"] }},
  "volume": "soft",
  "section_profiles": {{ "introduction": {{ "pitch": "-15%", "rate": "80%", "volume": "soft" }} }},
  "language_adjustments": {{ "es-ES": {{ "rate": "80%", "pitch": "-12%" }} }},
  "progression": {{ "start": {{ "rate": "85%", "pitch": "-10%" }} }}
}}

Just return the valid JSON."""
                
                fix_response = llm.invoke([HumanMessage(content=fix_prompt)])
                fix_content = fix_response.content
                
                # Try to extract and parse JSON again
                json_match = re.search(r'({.*}|\[.*\])', fix_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0).strip()
                else:
                    json_match = re.search(r'({.+})', fix_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                    else:
                        json_str = fix_content
                
                prosody_profile = json.loads(json_str)
                state["prosody_profile"] = prosody_profile
                state["parsing_warning"] = f"Used fallback parsing: {str(parsing_error)}"
                
            except Exception as fallback_error:
                # If all else fails, use a rule-based approach
                emotional_state = request["emotional_state"]
                meditation_style = request["meditation_style"]
                language_code = request["language_code"]
                
                # Default profile template
                prosody_profile = {
                    "pitch": {
                        "base_pitch": "-10%",
                        "range": "moderate",
                        "contour_pattern": "natural with moderate variation",
                        "emotional_contours": {
                            "calm": "gradual downward drift with gentle rises",
                            "anxious": "higher baseline with more variation",
                            "energetic": "higher baseline with upward contours",
                            "tired": "lower baseline with minimal variation",
                            "happy": "moderate baseline with upward contours",
                            "sad": "lower baseline with downward contours",
                            "stressed": "higher baseline with tense contours"
                        }
                    },
                    "rate": {
                        "base_rate": "85%",
                        "variation": "moderate",
                        "special_sections": {
                            "breathing": "70%",
                            "introduction": "80%",
                            "closing": "75%",
                            "grounding": "65%",
                            "body_scan": "60%",
                            "affirmations": "75%",
                            "visualization": "70%"
                        },
                        "emotional_rates": {
                            "calm": "70%",
                            "anxious": "85%",
                            "energetic": "90%",
                            "tired": "65%",
                            "happy": "85%",
                            "sad": "70%",
                            "stressed": "80%"
                        }
                    },
                    "pauses": {
                        "short_pause": "800ms",
                        "medium_pause": "2s",
                        "long_pause": "4s",
                        "breath_pause": "3s",
                        "sentence_pattern": "medium after statements, long after guidance",
                        "breathing_patterns": {
                            "4-7-8": {
                                "inhale": "4s",
                                "hold": "7s",
                                "exhale": "8s"
                            },
                            "box_breathing": {
                                "inhale": "4s",
                                "hold_in": "4s",
                                "exhale": "4s",
                                "hold_out": "4s"
                            },
                            "deep_breathing": {
                                "inhale": "4s",
                                "exhale": "6s"
                            }
                        }
                    },
                    "emphasis": {
                        "intensity": "moderate",
                        "key_terms": analysis.get("key_terms", ["breath", "relax", "present", "awareness"]),
                        "emotional_emphasis": {
                            "calm": "reduced",
                            "anxious": "moderate",
                            "energetic": "strong",
                            "tired": "reduced",
                            "happy": "moderate",
                            "sad": "reduced",
                            "stressed": "moderate"
                        }
                    },
                    "volume": "soft",
                    "voice_quality": "breathy",
                    "section_profiles": {
                        "introduction": {
                            "pitch": "-15%",
                            "rate": "80%",
                            "volume": "soft"
                        },
                        "grounding": {
                            "pitch": "-20%",
                            "rate": "65%",
                            "volume": "x-soft"
                        },
                        "body_scan": {
                            "pitch": "-18%",
                            "rate": "60%",
                            "volume": "x-soft"
                        },
                        "breathing": {
                            "pitch": "-15%",
                            "rate": "70%",
                            "volume": "soft"
                        },
                        "visualization": {
                            "pitch": "-12%",
                            "rate": "75%",
                            "volume": "soft"
                        },
                        "affirmations": {
                    "pitch": "-10%",
                            "rate": "75%",
                            "volume": "medium"
                        },
                        "closing": {
                            "pitch": "-15%",
                            "rate": "75%",
                            "volume": "soft"
                        }
                    },
                    "language_adjustments": {
                    "es-ES": {
                            "rate": "80%",
                            "pitch": "-12%",
                            "volume": "soft"
                    },
                    "en-US": {
                            "rate": "85%",
                            "pitch": "-10%",
                            "volume": "medium"
                        }
                    },
                    "progression": {
                        "start": {
                            "rate": "85%",
                            "pitch": "-10%",
                            "volume": "medium"
                        },
                        "middle": {
                            "rate": "75%",
                            "pitch": "-15%",
                            "volume": "soft"
                        },
                        "end": {
                            "rate": "70%",
                            "pitch": "-20%",
                            "volume": "x-soft"
                        }
                    }
                }
                
                # Make specific adjustments based on emotional state
                if emotional_state == "anxious":
                    prosody_profile["pitch"]["base_pitch"] = "-15%"
                    prosody_profile["rate"]["base_rate"] = "75%"
                    prosody_profile["volume"] = "x-soft"
                elif emotional_state == "energetic":
                    prosody_profile["pitch"]["base_pitch"] = "-5%"
                    prosody_profile["rate"]["base_rate"] = "90%"
                    prosody_profile["volume"] = "medium"
                
                # Adjust for meditation style
                if meditation_style == "Mindfulness":
                    prosody_profile["rate"]["base_rate"] = "75%"
                    prosody_profile["pauses"]["medium_pause"] = "2.5s"
                    prosody_profile["pauses"]["long_pause"] = "5s"
                elif meditation_style == "BreathFocus":
                    prosody_profile["section_profiles"]["breathing"]["rate"] = "65%"
                    prosody_profile["section_profiles"]["breathing"]["pitch"] = "-15%"
                    prosody_profile["section_profiles"]["breathing"]["volume"] = "x-soft"
                elif meditation_style == "BodyScan":
                    prosody_profile["rate"]["base_rate"] = "70%"
                    prosody_profile["section_profiles"]["body_scan"]["rate"] = "60%"
                    prosody_profile["section_profiles"]["body_scan"]["pitch"] = "-18%"
                
                # Apply language-specific adjustments
                if language_code in prosody_profile["language_adjustments"]:
                    lang_adjustments = prosody_profile["language_adjustments"][language_code]
                    prosody_profile["rate"]["base_rate"] = lang_adjustments["rate"]
                    prosody_profile["pitch"]["base_pitch"] = lang_adjustments["pitch"]
                    prosody_profile["volume"] = lang_adjustments["volume"]
                
                state["prosody_profile"] = prosody_profile
                state["profile_generation_error"] = f"Used template profile due to errors: {str(parsing_error)} → {str(fallback_error)}"
        
        logger.info("Completed prosody profile generation")
        log_state_transition("generate_prosody_profile_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error generating prosody profile: {str(e)}")
        state["error"] = f"Error generating prosody profile: {str(e)}"
        return state

def generate_ssml(state: GraphState) -> GraphState:
    """Generate optimized SSML markup using LLM with comprehensive SSML knowledge"""
    try:
        logger.info("Starting SSML generation")
        log_state_transition("generate_ssml", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        script = state["meditation_script"]
        profile = state["prosody_profile"]
        analysis = state["prosody_analysis"]
        
        # Use a more powerful LLM for SSML generation
        llm = ChatOpenAI(temperature=0.2, model="gpt-4o")
        
        # Create a system prompt with detailed SSML knowledge
        system_prompt = """You are an expert SSML generator for AWS Polly Neural voices. Your task is to create optimized SSML markup for meditation narration that will be synthesized using AWS Polly.

IMPORTANT CONSTRAINTS FOR AWS POLLY NEURAL VOICES:
1. Use only fully supported tags: <speak>, <break>, <prosody>, <p>, <s>
2. DO NOT use these unsupported tags: <emphasis>, <amazon:auto-breaths>, <amazon:effect name="whispered">, <amazon:effect phonation="soft">
3. For emphasis effects, use <prosody> with adjusted rate/pitch instead of <emphasis>
4. For breath sounds, use strategically placed <break> tags of appropriate durations
5. For soft/intimate speech, use <prosody volume="x-soft" rate="slow" pitch="low"> instead of whispered effects

SSML TECHNIQUES FOR MEDITATION:
1. Breathing instructions: 
   - Use slower rate: <prosody rate="60%">Breathe in slowly</prosody>
   - Follow with appropriate pauses: <break time="4s"/>
   - Match pause duration to instruction (longer for exhales, etc.)

2. Progressive relaxation:
   - Gradually slow rate and lower pitch throughout the meditation
   - For body scans: <prosody rate="65%" pitch="-15%">Feel your shoulders relax</prosody>

3. Section transitions:
   - Use paragraph tags for major sections: <p>New section content</p>
   - Add longer breaks between sections: <break time="3s"/>

4. Emotional resonance:
   - For calming: <prosody pitch="-15%" rate="70%" volume="soft">
   - For grounding: <prosody pitch="-20%" rate="65%" volume="x-soft">

5. Key terms and emphasis:
   - Important words: <prosody pitch="-5%" rate="90%">awareness</prosody>
   - Use subtle adjustments to avoid unnatural emphasis

6. Nested tags for combined effects:
   - <prosody rate="slow"><prosody pitch="low">Deeply relaxed</prosody></prosody>

7. CRITICAL TECHNICAL REQUIREMENTS:
   - All opening tags MUST have matching closing tags
   - Tags must be properly nested (inner tags close before outer tags)
   - Always include units for <break> times (e.g., "500ms" or "2s")
   - Percentage values must include the % symbol
   - Only use valid attribute values as specified above

Your SSML should create a natural, soothing meditation experience appropriate for the requested emotional state and style."""

        # Create a detailed human prompt with all relevant context
        human_prompt = f"""Generate optimal SSML markup for this meditation script that will be synthesized using AWS Polly Neural voices.

CONTEXT:
- Emotional state: {state['request']['emotional_state']}
- Meditation style: {state['request']['meditation_style']}
- Theme: {state['request']['meditation_theme']}
- Duration: {state['request']['duration_minutes']} minutes
- Language: {state['request']['language_code']}
- Voice: {state['request']['voice_type']} ({state['request']['language_code']})

PROSODY PROFILE:
{json.dumps(profile, indent=2)}

PROSODY ANALYSIS:
{json.dumps(analysis, indent=2)}

MEDITATION SCRIPT:
{script['content']}

Please generate complete, well-structured SSML with:
1. Appropriate prosody tags for each section based on the analysis
2. Strategic breaks for natural pacing and breathing guidance
3. Progressive changes in prosody throughout the meditation (slower/softer toward end)
4. Properly emphasized key terms using prosody adjustments (not emphasis tags)
5. Special treatment for breathing instructions with appropriate pause durations
6. Optimized structure with paragraph and sentence tags where appropriate
7. MOST IMPORTANTLY: Ensure all tags are balanced and properly nested

Return only the complete SSML markup inside <speak> tags, fully ready for AWS Polly Neural voice synthesis."""

        # Generate the SSML
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        logger.info("Requesting SSML generation")
        response = llm.invoke(messages)
        
        # Log the SSML generation interaction
        log_llm_interaction(
            prompt=human_prompt,
            response_content=response.content,
            model=llm.model_name,
            purpose="SSML Generation"
        )
        
        # Extract SSML from response
        content = response.content
        
        # Simple extraction of SSML - we'll rely on the review step for fixing any issues
        import re
        ssml_match = re.search(r'<speak>.*?</speak>', content, re.DOTALL)
        
        if ssml_match:
            ssml = ssml_match.group(0)
        else:
            # If no tags found, wrap the content in speak tags
            if "<prosody" in content and "<break" in content:
                ssml = f"<speak>\n{content}\n</speak>"
            else:
                # If extraction fails, create a simple SSML wrapper
                ssml = f"<speak>\n{content}\n</speak>"
                logger.warning("Could not extract proper SSML - creating basic wrapper")
        
        # Store the SSML for review in the next step
        state["ssml_output"] = ssml
        logger.info(f"Completed initial SSML generation with {len(ssml)} characters")
        logger.info("The SSML will be reviewed and improved in the next step")
        log_state_transition("generate_ssml_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error generating SSML: {str(e)}")
        state["error"] = f"Error generating SSML: {str(e)}"
        return state

def detect_breathing_pattern(sentence: str) -> Optional[Dict[str, Any]]:
    """Detect breathing pattern instructions in a sentence"""
    sentence_lower = sentence.lower()
    
    # 4-7-8 breathing pattern
    if any(phrase in sentence_lower for phrase in ["inhala por 4", "inhale for 4", "breathe in for 4"]):
        return {
            "type": "4-7-8",
            "phase": "inhale"
        }
    elif any(phrase in sentence_lower for phrase in ["mantén por 7", "hold for 7", "hold your breath for 7"]):
        return {
            "type": "4-7-8",
            "phase": "hold"
        }
    elif any(phrase in sentence_lower for phrase in ["exhala por 8", "exhale for 8", "breathe out for 8"]):
        return {
            "type": "4-7-8",
            "phase": "exhale"
        }
    
    # Box breathing pattern
    elif any(phrase in sentence_lower for phrase in ["inhala por 4", "inhale for 4", "breathe in for 4"]):
        return {
            "type": "box_breathing",
            "phase": "inhale"
        }
    elif any(phrase in sentence_lower for phrase in ["mantén por 4", "hold for 4", "hold your breath for 4"]):
        return {
            "type": "box_breathing",
            "phase": "hold_in"
        }
    elif any(phrase in sentence_lower for phrase in ["exhala por 4", "exhale for 4", "breathe out for 4"]):
        return {
            "type": "box_breathing",
            "phase": "exhale"
        }
    
    # Deep breathing pattern
    elif any(phrase in sentence_lower for phrase in ["respiración profunda", "deep breath", "deep breathing"]):
        return {
            "type": "deep_breathing",
            "phase": "inhale"
        }
    
    return None

def generate_meditation_audio(state: GraphState) -> GraphState:
    """Generate audio from SSML using AWS Polly"""
    try:
        logger.info("Starting audio generation")
        log_state_transition("generate_meditation_audio", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
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
        voice_id = voice_map.get(voice_type.value, voice_map[VoiceType.NEUTRAL.value])
        
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
            logger.info(f"Generated audio file: {audio_file}")
        else:
            state["error"] = "Failed to generate audio"
            logger.error("Failed to generate audio")
            
        log_state_transition("generate_meditation_audio_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error generating audio: {str(e)}")
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
        logger.info("Starting audio mixing")
        log_state_transition("mix_with_soundscape", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
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
            
            logger.info(f"Mixed audio files: Full={full_audio}, Sample={sample_audio}")
            
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
            logger.info(f"Saved complete state to JSON: {json_file}")
        else:
            state["error"] = "Failed to mix audio with soundscape (ffmpeg)"
            logger.error("Failed to mix audio with soundscape")
            
        log_state_transition("mix_with_soundscape_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error mixing audio (ffmpeg): {str(e)}")
        state["error"] = f"Error mixing audio (ffmpeg): {str(e)}"
        return state

def run_workflow_step(step: str, state: Optional[GraphState] = None) -> GraphState:
    """Run a single step of the workflow"""
    logger.info(f"Running workflow step: {step}")
    
    if step not in WORKFLOW_STEPS:
        error_msg = f"Invalid step: {step}. Must be one of {WORKFLOW_STEPS}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Load state if not provided
    if state is None:
        # Try to load the latest state from the previous step
        prev_step_idx = WORKFLOW_STEPS.index(step) - 1
        if prev_step_idx >= 0:
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            state_file = get_latest_state_file(prev_step)
            if state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {state_file})")
                state = load_state(state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from {state_file}")
            else:
                logger.warning(f"No state file found for previous step: {prev_step}")
    
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
    
    # Log the state before running
    logger.info(f"State before workflow step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
    
    # Create workflow graph
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("generate_script", generate_meditation_script)
    workflow.add_node("analyze_prosody", analyze_prosody_needs)
    workflow.add_node("create_profile", generate_prosody_profile)
    workflow.add_node("generate_ssml", generate_ssml)
    workflow.add_node("review_and_improve_ssml", review_and_improve_ssml)  # Add the new step
    workflow.add_node("generate_audio", generate_meditation_audio)
    workflow.add_node("mix_audio", mix_with_soundscape)
    
    # Configure the workflow edges
    workflow.add_edge("generate_script", "analyze_prosody")
    workflow.add_edge("analyze_prosody", "create_profile")
    workflow.add_edge("create_profile", "generate_ssml")
    workflow.add_edge("generate_ssml", "review_and_improve_ssml")  # Connect generate_ssml to review step
    workflow.add_edge("review_and_improve_ssml", "generate_audio")  # Connect review step to generate_audio
    workflow.add_edge("generate_audio", "mix_audio")
    workflow.add_edge("mix_audio", END)
    
    # Set entry point
    workflow.set_entry_point(step)
    
    # Compile and run
    compiled_workflow = workflow.compile()
    logger.info(f"Invoking workflow at step: {step}")
    result = compiled_workflow.invoke(state)
    
    # Save state after step completion
    state_file = save_state(result, step)
    logger.info(f"Saved state to: {state_file}")
    
    return result

def run_meditation_generation(request_data: Dict[str, Any], start_step: Optional[str] = None, end_step: Optional[str] = None) -> Dict[str, Any]:
    """Run the meditation generation process, optionally starting from a specific step"""
    logger.info(f"Starting meditation generation process from step: {start_step or WORKFLOW_STEPS[0]}")
    if end_step:
        logger.info(f"Will stop after step: {end_step}")
    logger.info(f"Request: {json.dumps(request_data)}")
    
    # Create and run a custom workflow based on start_step and end_step
    if end_step and end_step in WORKFLOW_STEPS:
        # Find the indices of the start and end steps
        start_idx = WORKFLOW_STEPS.index(start_step) if start_step and start_step in WORKFLOW_STEPS else 0
        end_idx = WORKFLOW_STEPS.index(end_step)
        
        # Create a list of steps to run
        steps_to_run = WORKFLOW_STEPS[start_idx:end_idx+1]
        logger.info(f"Running steps: {steps_to_run}")
        
        # Try to load state from previous step if starting in the middle
        state = None
        if start_step and start_step in WORKFLOW_STEPS and WORKFLOW_STEPS.index(start_step) > 0:
            prev_step_idx = WORKFLOW_STEPS.index(start_step) - 1
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            prev_state_file = get_latest_state_file(prev_step)
            
            if prev_state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {prev_state_file})")
                state = load_state(prev_state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from previous step: {prev_step}")
        
        # Initialize state if not loaded from previous step
        if state is None:
            state = {
                "request": request_data,
                "meditation_script": None,
                "prosody_analysis": None,
                "prosody_profile": None,
                "ssml_output": None,
                "audio_output": None,
                "error": None,
                "current_step": steps_to_run[0]
            }
        else:
            # Update request data in loaded state
            state["request"] = request_data
            state["current_step"] = steps_to_run[0]
            state["error"] = None
        
        # Run each step sequentially
        for step in steps_to_run:
            state["current_step"] = step
            logger.info(f"Running step: {step}")
            logger.info(f"State before step: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
            state = run_single_step(step, state)
            if state.get("error"):
                logger.error(f"Error in step {step}: {state.get('error')}")
                return state
        
        return state
    elif start_step and start_step in WORKFLOW_STEPS:
        # Traditional flow from start_step
        # Try to load state from previous step
        state = None
        if WORKFLOW_STEPS.index(start_step) > 0:
            prev_step_idx = WORKFLOW_STEPS.index(start_step) - 1
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            prev_state_file = get_latest_state_file(prev_step)
            
            if prev_state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {prev_state_file})")
                state = load_state(prev_state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from previous step: {prev_step}")
        
        # Initialize state if not loaded
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
        else:
            # Update request data in loaded state
            state["request"] = request_data
            state["current_step"] = start_step
            state["error"] = None
            
        # Log what's in the state before running
        logger.info(f"State before running step {start_step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
        
        return run_workflow_step(start_step, state)
    else:
        # Full workflow from beginning
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

def run_single_step(step: str, state: GraphState) -> GraphState:
    """Run a single step of the workflow without chaining to the next step"""
    logger.info(f"Running single step: {step}")
    
    # Map steps to functions
    step_functions = {
        "generate_script": generate_meditation_script,
        "analyze_prosody": analyze_prosody_needs,
        "create_profile": generate_prosody_profile,
        "generate_ssml": generate_ssml,
        "review_and_improve_ssml": review_and_improve_ssml,  # Add the new step
        "generate_audio": generate_meditation_audio,
        "mix_audio": mix_with_soundscape
    }
    
    # Log state before running
    logger.info(f"State before single step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
    
    # Run the step
    if step in step_functions:
        state = step_functions[step](state)
        save_state_path = save_state(state, step)
        logger.info(f"Saved state after step {step} to: {save_state_path}")
        
        # Log state after running
        logger.info(f"State after single step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
        
        return state
    else:
        state["error"] = f"Unknown step: {step}"
        return state

def review_and_improve_ssml(state: GraphState) -> GraphState:
    """Review generated SSML for issues and improve it according to best practices"""
    try:
        logger.info("Starting SSML review and improvement")
        log_state_transition("review_and_improve_ssml", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        if not state.get("ssml_output"):
            state["error"] = "No SSML output to review"
            return state
            
        # Get the current SSML
        ssml = state["ssml_output"]
        
        # Initialize LLM for review
        llm = ChatOpenAI(temperature=0.2, model="gpt-4o")
        
        # Create system prompt with SSML best practices knowledge
        system_prompt = """You are an expert SSML reviewer and fixer specializing in meditation audio. Your task is to analyze SSML markup, identify and fix any issues, particularly for AWS Polly Neural voices used in meditation applications.

When reviewing SSML, focus first on technical correctness:

1. Technical Correctness (HIGHEST PRIORITY):
   - Fix any unbalanced tags (unclosed <prosody>, <p>, or <s> tags)
   - Fix duplicate closing tags or incorrect nesting order
   - Fix improper value formats (e.g., missing % symbol in percentages)
   - Fix missing units in <break> durations (should use "ms" or "s")
   - Fix invalid attribute values (e.g., outside supported ranges)
   - Ensure compatibility with AWS Polly Neural voices

2. Tag compatibility with Neural voices:
   - Neural voices support: <speak>, <break>, <prosody>, <p>, <s>, <say-as>, <phoneme>, <w>, <lang>, <mark>, <sub>
   - Neural voices DO NOT support: <emphasis>, <amazon:auto-breaths>, <amazon:effect name="whispered">, <phonation>
   - Replace unsupported tags with allowed alternatives

3. Meditation-specific best practices:
   - Progressive slowing of rate throughout meditation (<prosody rate> gradually decreasing)
   - Appropriate pause durations after breathing instructions (<break> of 3-6s)
   - Lower pitch for relaxation sections (<prosody pitch> between -10% and -20%)
   - Softer volume for deeper sections (<prosody volume> using "soft" or "x-soft")
   - Proper pacing for body scan sections (slower rate, longer breaks)

Provide a corrected and improved version of the SSML that maintains the meditation's content and intent while ensuring technical correctness."""

        # Iterative improvement cycle
        max_iterations = 3
        iteration_count = 0
        issues_fixed = []
        
        while iteration_count < max_iterations:
            iteration_count += 1
            logger.info(f"Starting SSML review iteration {iteration_count}")
            
            # Create review prompt with current SSML
            review_prompt = f"""Review and fix the following SSML for a meditation:

```xml
{ssml}
```

Focus on these priorities in order:
1. Technical correctness - Fix ALL unbalanced tags, nesting issues, or invalid values (CRITICAL)
2. AWS Polly Neural voice compatibility - Replace any unsupported tags
3. Meditation experience enhancement - Improve pacing, prosody, pauses

If you find technical issues, fix them ALL and provide a complete corrected SSML.
If there are no technical issues but you find opportunities to enhance the meditation experience, make those improvements.
If the SSML looks technically correct and well-optimized, state that no improvements are needed.

Return your analysis followed by the complete improved SSML. The SSML MUST be valid XML that can be parsed without errors."""
            
            # Get the review and improved SSML
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=review_prompt)
            ]
            
            logger.info(f"Requesting SSML review iteration {iteration_count}")
            response = llm.invoke(messages)
            
            # Log the review interaction
            log_llm_interaction(
                prompt=review_prompt,
                response_content=response.content,
                model=llm.model_name,
                purpose=f"SSML Review Iteration {iteration_count}"
            )
            
            # Extract the analysis and improved SSML
            content = response.content
            
            # Check if no improvements needed
            if "no improvements are needed" in content.lower() or "ssml looks good" in content.lower():
                logger.info("SSML review complete - No further improvements needed")
                issues_fixed.append(f"Iteration {iteration_count}: No issues found")
                break
                
            # Try to extract improved SSML
            import re
            ssml_match = re.search(r'```xml\s*(<speak>.*?</speak>)\s*```', content, re.DOTALL)
            
            if not ssml_match:
                # Try alternative format without code blocks
                ssml_match = re.search(r'<speak>.*?</speak>', content, re.DOTALL)
            
            if ssml_match:
                # Extract issues identified
                analysis_text = content.split("```xml")[0] if "```xml" in content else "Improvements made to SSML"
                issues_fixed.append(f"Iteration {iteration_count}: {analysis_text.strip()}")
                
                # Update the SSML
                improved_ssml = ssml_match.group(1) if "```xml" in content else ssml_match.group(0)
                ssml = improved_ssml
                logger.info(f"SSML updated in iteration {iteration_count}")
            else:
                # If no improved SSML found, make a direct request for valid SSML
                fix_prompt = f"""I need ONLY the complete fixed SSML for the meditation with no explanation. The SSML must be syntactically valid XML with balanced tags and proper nesting.

Original SSML:
{ssml}

Return only the complete SSML, surrounded by <speak> tags."""
                
                fix_response = llm.invoke([HumanMessage(content=fix_prompt)])
                fix_content = fix_response.content
                
                # Try to extract again
                ssml_match = re.search(r'<speak>.*?</speak>', fix_content, re.DOTALL)
                if ssml_match:
                    improved_ssml = ssml_match.group(0)
                    ssml = improved_ssml
                    issues_fixed.append(f"Iteration {iteration_count}: Extracted fixed SSML")
                    logger.info(f"SSML extracted in iteration {iteration_count}")
                else:
                    # Last resort: Simplify the SSML structure completely
                    logger.warning("Could not extract improved SSML, creating simplified version")
                    
                    # Create a simplified but valid SSML document
                    final_fix_prompt = f"""Create a simplified but valid SSML for this meditation text, using only basic paragraph and prosody tags. Return only valid SSML:

Text:
{re.sub(r'<[^>]+>', '', ssml)}"""
                    
                    final_response = llm.invoke([HumanMessage(content=final_fix_prompt)])
                    final_content = final_response.content
                    
                    # Extract one more time
                    final_match = re.search(r'<speak>.*?</speak>', final_content, re.DOTALL)
                    if final_match:
                        ssml = final_match.group(0)
                        issues_fixed.append(f"Iteration {iteration_count}: Created simplified SSML structure")
                        logger.info("Created simplified SSML structure")
                        break
                    else:
                        issues_fixed.append(f"Iteration {iteration_count}: Failed to create valid SSML")
                        logger.error("Failed to create valid SSML")
                        break
        
        # Update the state with the improved SSML
        state["ssml_output"] = ssml
        state["ssml_review"] = {
            "iterations": iteration_count,
            "issues_fixed": issues_fixed
        }
        
        logger.info(f"Completed SSML review after {iteration_count} iterations")
        log_state_transition("review_and_improve_ssml_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error reviewing SSML: {str(e)}")
        state["error"] = f"Error reviewing SSML: {str(e)}"
        return state

if __name__ == "__main__":
    # Example usage
    request_data = {
        "emotional_state": EmotionalState.ANXIOUS.value,
        "meditation_style": MeditationStyle.MINDFULNESS.value,
        "meditation_theme": MeditationTheme.STRESS_RELIEF.value,
        "duration_minutes": 10,
        "voice_type": VoiceType.FEMALE.value,
        "language_code": "en-US",
        "soundscape": SoundscapeType.NATURE.value
    }
    
    result = run_meditation_generation(request_data)
    print(json.dumps(result, indent=2)) 