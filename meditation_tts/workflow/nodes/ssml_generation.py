"""
SSML generation node for the workflow.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, log_llm_interaction, logger

def generate_ssml(state: GraphState) -> GraphState:
    """
    Generate optimized SSML markup using LLM with comprehensive SSML knowledge.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with SSML output
    """
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