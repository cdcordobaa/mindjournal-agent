"""
Prosody profile generation node for the workflow.
"""

import re
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, log_llm_interaction, logger

def generate_prosody_profile(state: GraphState) -> GraphState:
    """
    Generate a comprehensive prosody profile using LLM to consider all contextual factors.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with prosody profile
    """
    try:
        logger.info("Starting prosody profile generation")
        log_state_transition("generate_prosody_profile", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        request = state["request"]
        analysis = state["prosody_analysis"]
        
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
  "pitch": { "base_pitch": "-10%", "range": "moderate", "contour_pattern": "gradual downward drift with gentle rises", "emotional_contours": { "calm": "gradual downward drift with gentle rises", "anxious": "higher baseline with more variation", "energetic": "higher baseline with upward contours", "tired": "lower baseline with minimal variation", "happy": "moderate baseline with upward contours", "sad": "lower baseline with downward contours", "stressed": "higher baseline with tense contours" } },
  "rate": { "base_rate": "85%", "variation": "moderate", "special_sections": { "breathing": "70%", "introduction": "80%", "closing": "75%", "grounding": "65%", "body_scan": "60%", "affirmations": "75%", "visualization": "70%" }, "emotional_rates": { "calm": "70%", "anxious": "85%", "energetic": "90%", "tired": "65%", "happy": "85%", "sad": "70%", "stressed": "80%" } },
  "pauses": { "short_pause": "800ms", "medium_pause": "2s", "long_pause": "4s", "breath_pause": "3s", "sentence_pattern": "medium after statements, long after guidance", "breathing_patterns": { "4-7-8": { "inhale": "4s", "hold": "7s", "exhale": "8s" }, "box_breathing": { "inhale": "4s", "hold_in": "4s", "exhale": "4s", "hold_out": "4s" }, "deep_breathing": { "inhale": "4s", "exhale": "6s" } } },
  "emphasis": { "intensity": "moderate", "key_terms": ["awareness", "breath", "present"], "emotional_emphasis": { "calm": "reduced", "anxious": "moderate", "energetic": "strong", "tired": "reduced", "happy": "moderate", "sad": "reduced", "stressed": "moderate" } },
  "volume": "soft",
  "voice_quality": "breathy",
  "section_profiles": { "introduction": { "pitch": "-15%", "rate": "80%", "volume": "soft" }, "grounding": { "pitch": "-20%", "rate": "65%", "volume": "x-soft" }, "body_scan": { "pitch": "-18%", "rate": "60%", "volume": "x-soft" }, "breathing": { "pitch": "-15%", "rate": "70%", "volume": "soft" }, "visualization": { "pitch": "-12%", "rate": "75%", "volume": "soft" }, "affirmations": { "pitch": "-10%", "rate": "75%", "volume": "medium" }, "closing": { "pitch": "-15%", "rate": "75%", "volume": "soft" } },
  "language_adjustments": { "es-ES": { "rate": "80%", "pitch": "-12%", "volume": "soft" }, "en-US": { "rate": "85%", "pitch": "-10%", "volume": "medium" } },
  "progression": { "start": { "rate": "85%", "pitch": "-10%", "volume": "medium" }, "middle": { "rate": "75%", "pitch": "-15%", "volume": "soft" }, "end": { "rate": "70%", "pitch": "-20%", "volume": "x-soft" } }
}
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