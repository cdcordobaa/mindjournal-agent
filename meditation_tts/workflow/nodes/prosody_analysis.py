"""
Prosody analysis node for the workflow.
"""

import re
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, log_llm_interaction, logger

def analyze_prosody_needs(state: GraphState) -> GraphState:
    """
    Analyze the script to determine prosody needs using sophisticated LLM analysis.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with prosody analysis
    """
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