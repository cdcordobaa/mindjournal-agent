# Advanced Prosody System Implementation with LangGraph
# This implements a sophisticated prosody control system for meditation applications

import os
import json
import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.output_parsers import PydanticOutputParser

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

class Duration(BaseModel):
    minutes: int

class SessionType(str, Enum):
    USER_GENERATED = "UserGenerated"
    CATALOG = "Catalog"

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

class RateProfile(BaseModel):
    base_rate: str = Field(description="Base speech rate, e.g. '80%', 'slow'")
    variation: str = Field(description="How much the rate varies, e.g. 'minimal', 'moderate'")
    special_sections: Dict[str, str] = Field(
        description="Special rate settings for specific sections like breathing instructions"
    )

class PauseProfile(BaseModel):
    short_pause: str = Field(description="Duration for short pauses, e.g. '500ms'")
    medium_pause: str = Field(description="Duration for medium pauses, e.g. '1s'")
    long_pause: str = Field(description="Duration for long pauses, e.g. '3s'")
    breath_pause: str = Field(description="Duration for breathing instruction pauses, e.g. '4s'")
    sentence_pattern: str = Field(description="Pattern for sentence pauses, e.g. 'medium after statements, long after questions'")

class EmphasisProfile(BaseModel):
    intensity: str = Field(description="Overall emphasis intensity, e.g. 'strong', 'moderate', 'soft'")
    key_terms: List[str] = Field(description="List of terms that should receive special emphasis")

class ProsodyProfile(BaseModel):
    """Complete prosody profile for a specific emotional state and meditation context"""
    pitch: PitchProfile
    rate: RateProfile
    pauses: PauseProfile
    emphasis: EmphasisProfile
    volume: str = Field(description="Overall volume setting, e.g. 'soft', 'medium', '+5dB'")
    voice_quality: Optional[str] = Field(default=None, description="Voice quality hint if supported, e.g. 'breathy', 'warm'")
    
    # Section-specific profiles
    intro_adjustments: Dict[str, str] = Field(description="Specific adjustments for introduction section")
    body_adjustments: Dict[str, str] = Field(description="Specific adjustments for main body section")
    closing_adjustments: Dict[str, str] = Field(description="Specific adjustments for closing section")
    
    # Language-specific adjustments
    language_adjustments: Dict[str, Dict[str, str]] = Field(
        description="Adjustments specific to each language code"
    )

# ============ LangGraph State Model ============

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
    error: Optional[str]

# ============ LangGraph Node Functions ============

def generate_meditation_script(state: GraphState) -> GraphState:
    """Generate the raw meditation script based on the request parameters"""
    try:
        # Initialize the LLM
        llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        
        # Create a system prompt for meditation generation
        system_prompt = """You are an expert multilingual meditation guide. Your task is to create meditation scripts 
        tailored to the user's needs and preferences. Ensure that the language used is natural and 
        fluent for native speakers of the target language.
        
        Create a meditation script that is:
        1. Divided into clear sections (introduction, main guidance, breathing sections, closing)
        2. Includes appropriate pauses for breathing instructions
        3. Uses language appropriate for the emotional state and meditation style
        4. Is the appropriate length for the specified duration
        5. Incorporates the meditation theme naturally throughout
        
        Each section should be separated by blank lines.
        Include timestamps for soundscape sections (e.g., "(2 minutes of nature sounds)")."""
        
        # Create the human prompt with parameters
        request = state["request"]
        human_prompt = f"""Create a meditation script based on the following parameters:

        Emotional State: {request["emotional_state"]}
        Duration: {request["duration_minutes"]} minutes
        Meditation Style: {request["meditation_style"]}
        Meditation Theme: {request["meditation_theme"]}
        Language: {request["language_code"]}
        
        Remember to create natural pauses for breathing instructions and divide the script into clear sections."""
        
        # Generate the meditation script
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        raw_response = llm.invoke(messages)
        
        # Process the script to identify sections
        script_content = raw_response.content
        script_sections = []
        
        # Simple section identification - in production, this would be more sophisticated
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
            
        # Initialize the LLM
        llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        
        # Create the system prompt
        system_prompt = """You are an expert in speech prosody and meditation guidance. 
        Your task is to analyze a meditation script and determine the optimal prosody parameters
        that would make the meditation most effective for the given emotional state and style.
        
        Focus on:
        1. Overall tone needed for this meditation
        2. Key terms that should receive emphasis
        3. Breathing patterns that need special prosodic treatment
        4. Points where emphasis would be most effective
        5. Different characteristics needed for each section of the meditation"""
        
        # Create the prompt with the script and parameters
        request = state["request"]
        script = state["meditation_script"]["content"]
        
        human_prompt = f"""Analyze the following meditation script and provide detailed prosody recommendations.
        
        Emotional State of User: {request["emotional_state"]}
        Meditation Style: {request["meditation_style"]}
        Meditation Theme: {request["meditation_theme"]}
        Language: {request["language_code"]}
        
        MEDITATION SCRIPT:
        {script}
        
        Provide a structured analysis with the following:
        1. Overall tone recommendation
        2. List of key terms that should be emphasized
        3. Breathing pattern identification and recommendations
        4. Points requiring special emphasis
        5. Different prosody needs for each section"""
        
        # Configure the pydantic parser
        parser = PydanticOutputParser(pydantic_object=ProsodyAnalysis)
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
        # This could be expanded into a more sophisticated mapping system
        emotional_state = request["emotional_state"]
        
        # Default profile for anxious state - would have profiles for all states in production
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
                        "rate": "80%",  # Spanish often needs slightly slower rate
                        "pitch": "-12%"
                    },
                    "en-US": {
                        "rate": "85%",
                        "pitch": "-10%"
                    }
                }
            )
        elif emotional_state == EmotionalState.STRESSED.value:
            profile = ProsodyProfile(
                pitch=PitchProfile(
                    base_pitch="-15%",
                    range="narrow",
                    contour_pattern="smooth with minimal variation"
                ),
                rate=RateProfile(
                    base_rate="75%",
                    variation="minimal",
                    special_sections={
                        "breathing": "65%",
                        "introduction": "70%",
                        "closing": "70%"
                    }
                ),
                pauses=PauseProfile(
                    short_pause="1s",
                    medium_pause="3s",
                    long_pause="5s",
                    breath_pause="4s",
                    sentence_pattern="longer than usual for all pauses"
                ),
                emphasis=EmphasisProfile(
                    intensity="soft",
                    key_terms=analysis["key_terms"]
                ),
                volume="soft",
                voice_quality="smooth",
                intro_adjustments={
                    "pitch": "-20%",
                    "rate": "70%"
                },
                body_adjustments={
                    "pitch": "-15%",
                    "rate": "75%"
                },
                closing_adjustments={
                    "pitch": "-20%",
                    "rate": "70%"
                },
                language_adjustments={
                    "es-ES": {
                        "rate": "70%",
                        "pitch": "-18%"
                    },
                    "en-US": {
                        "rate": "75%",
                        "pitch": "-15%"
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
        
        # Add recommended emphasis points from analysis
        for emphasis_point in analysis["recommended_emphasis_points"]:
            if "text" in emphasis_point:
                profile.emphasis.key_terms.append(emphasis_point["text"])
        
        # Apply language-specific adjustments
        language_code = request["language_code"]
        if language_code in profile.language_adjustments:
            language_adj = profile.language_adjustments[language_code]
            # In a full implementation, this would update the profile more comprehensively
        
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
                    "pitch": profile["pitch"]["base_pitch"] if profile["intro_adjustments"].get("pitch") is None else profile["intro_adjustments"]["pitch"],
                    "rate": profile["rate"]["base_rate"] if profile["intro_adjustments"].get("rate") is None else profile["intro_adjustments"]["rate"],
                    "volume": profile["volume"]
                }
            elif section_type == "closing":
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"] if profile["closing_adjustments"].get("pitch") is None else profile["closing_adjustments"]["pitch"],
                    "rate": profile["rate"]["base_rate"] if profile["closing_adjustments"].get("rate") is None else profile["closing_adjustments"]["rate"],
                    "volume": profile["volume"]
                }
            elif section_type == "breathing":
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"],
                    "rate": profile["rate"]["special_sections"].get("breathing", profile["rate"]["base_rate"]),
                    "volume": profile["volume"]
                }
            else:  # body or other
                section_profile = {
                    "pitch": profile["pitch"]["base_pitch"] if profile["body_adjustments"].get("pitch") is None else profile["body_adjustments"]["pitch"],
                    "rate": profile["rate"]["base_rate"] if profile["body_adjustments"].get("rate") is None else profile["body_adjustments"]["rate"],
                    "volume": profile["volume"]
                }
            
            # Add the section with prosody
            ssml += f'<prosody rate="{section_profile["rate"]}" pitch="{section_profile["pitch"]}" volume="{section_profile["volume"]}">\n'
            
            # Process the content
            # Split into sentences
            sentences = split_into_sentences(content)
            for sentence in sentences:
                processed_sentence = sentence
                
                # Add emphasis for key terms
                for term in profile["emphasis"]["key_terms"]:
                    if term.lower() in processed_sentence.lower():
                        processed_sentence = processed_sentence.replace(
                            term, 
                            f'<emphasis level="{profile["emphasis"]["intensity"]}">{term}</emphasis>'
                        )
                
                # Add the sentence to SSML
                ssml += processed_sentence
                
                # Add appropriate pause based on context
                if "inhala" in sentence.lower() or "exhala" in sentence.lower():
                    ssml += f' <break time="{profile["pauses"]["breath_pause"]}"/>\n'
                elif sentence.endswith("?"):
                    ssml += f' <break time="{profile["pauses"]["medium_pause"]}"/>\n'
                elif sentence.endswith("."):
                    ssml += f' <break time="{profile["pauses"]["short_pause"]}"/>\n'
                else:
                    ssml += "\n"
            
            # Handle special soundscape sections
            if section_type == "soundscape" and any(marker in content.lower() for marker in ["minutos", "minutes"]):
                # Extract duration if possible
                import re
                duration_match = re.search(r'(\d+)\s*minutos', content.lower()) or re.search(r'(\d+)\s*minutes', content.lower())
                if duration_match:
                    duration_min = int(duration_match.group(1))
                    duration_sec = duration_min * 60
                    ssml += f'<break time="{duration_sec}s"/>\n'
                else:
                    ssml += f'<break time="60s"/>\n'
            
            # Close the prosody tag for this section
            ssml += "</prosody>\n\n"
            
            # Add a longer pause between sections
            ssml += f'<break time="{profile["pauses"]["long_pause"]}"/>\n\n'
        
        # Close the SSML
        ssml += "</speak>"
        
        state["ssml_output"] = ssml
        return state
        
    except Exception as e:
        state["error"] = f"Error generating SSML: {str(e)}"
        return state

def split_into_sentences(text):
    """Simple sentence splitter - would be more sophisticated in production"""
    import re
    # Split on periods, question marks, and exclamation points
    # but keep the punctuation with the sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty sentences
    return [s for s in sentences if s.strip()]

# ============ LangGraph Construction ============

def create_prosody_graph():
    """Create the LangGraph for prosody generation"""
    # Initialize the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes to the graph
    workflow.add_node("generate_script", generate_meditation_script)
    workflow.add_node("analyze_prosody", analyze_prosody_needs)
    workflow.add_node("create_profile", generate_prosody_profile)
    workflow.add_node("generate_ssml", generate_ssml)
    
    # Add edges to the graph
    workflow.add_edge("generate_script", "analyze_prosody")
    workflow.add_edge("analyze_prosody", "create_profile")
    workflow.add_edge("create_profile", "generate_ssml")
    workflow.add_edge("generate_ssml", END)
    
    # Add error handling (in a real implementation, we might have recovery paths)
    workflow.set_entry_point("generate_script")
    
    # Compile the graph
    prosody_app = workflow.compile()
    
    return prosody_app

# ============ Helper Functions ============

def create_test_request():
    """Create a test request for demonstration"""
    return {
        "emotional_state": EmotionalState.ANXIOUS.value,
        "meditation_style": MeditationStyle.MINDFULNESS.value,
        "meditation_theme": MeditationTheme.STRESS_RELIEF.value,
        "duration_minutes": 10,
        "voice_type": VoiceType.FEMALE.value,
        "language_code": "es-ES",
        "soundscape": SoundscapeType.NATURE.value
    }

def run_prosody_generation(request_data):
    """Run the prosody generation process with the given request"""
    prosody_app = create_prosody_graph()
    
    # Create the initial state
    initial_state = {
        "request": request_data,
        "meditation_script": None,
        "prosody_analysis": None,
        "prosody_profile": None,
        "ssml_output": None,
        "error": None
    }
    
    # Execute the graph
    result = prosody_app.invoke(initial_state)
    
    return result

def demo_prosody_system():
    """Run a demonstration of the prosody system"""
    print("Demonstrating Advanced Prosody System with LangGraph")
    print("===================================================")
    
    # Create a test request
    test_request = create_test_request()
    print(f"Test Request: {json.dumps(test_request, indent=2)}")
    
    # Run the prosody generation
    print("\nRunning prosody generation...")
    result = run_prosody_generation(test_request)
    
    # Display the results
    if result.get("error"):
        print(f"\nError: {result['error']}")
    else:
        print("\nGeneration completed successfully!")
        
        print("\nGenerated Meditation Script:")
        print("----------------------------")
        print(result["meditation_script"]["content"])
        
        print("\nProsody Analysis:")
        print("----------------")
        print(json.dumps(result["prosody_analysis"], indent=2))
        
        print("\nGenerated SSML (excerpt):")
        print("-----------------------")
        ssml_lines = result["ssml_output"].split("\n")
        print("\n".join(ssml_lines[:20]) + "\n...\n" + "\n".join(ssml_lines[-10:]))
    
    return result

# For demonstration purposes
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Use the API key from environment variables
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key or set it manually.")
        exit(1)
    
    # Run the demonstration
    result = demo_prosody_system()
    
    # Save the output to a file for review
    with open("prosody_output.json", "w") as f:
        json.dump(result, f, indent=2)