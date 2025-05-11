"""
Audio generation node for the workflow.
"""

import os
import logging
from typing import Dict, Any, Optional

from meditation_tts.models.state import GraphState
from meditation_tts.models.enums import VoiceType
from meditation_tts.utils.logging_utils import log_state_transition, logger
from meditation_tts.config.constants import AUDIO_OUTPUT_DIR
from meditation_tts.services.audio_generator import AudioGenerator

def generate_meditation_audio(state: GraphState) -> GraphState:
    """
    Generate audio from SSML using AWS Polly.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with audio output information
    """
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
        
        # Check SSML length and use chunked audio generation if needed
        ssml_text = state["ssml_output"]
        logger.info(f"SSML length: {len(ssml_text)} characters")
        
        # Use the chunked audio generator which will handle splitting if needed
        audio_file = generator.generate_chunked_audio(
            ssml_text=ssml_text,
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