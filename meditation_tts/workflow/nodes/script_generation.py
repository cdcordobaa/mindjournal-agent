"""
Meditation script generation node for the workflow.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, log_llm_interaction, logger

def generate_meditation_script(state: GraphState) -> GraphState:
    """
    Generate a detailed meditation script with LLM including section identification.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with meditation script
    """
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
        state["meditation_script"] = {
            "content": script_content,
            "sections": script_sections
        }
        
        logger.info(f"Completed script generation with {len(script_sections)} sections")
        log_state_transition("generate_meditation_script_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error generating meditation script: {str(e)}")
        state["error"] = f"Error generating meditation script: {str(e)}"
        return state 