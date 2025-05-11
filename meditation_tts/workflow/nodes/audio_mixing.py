"""
Audio mixing node for the workflow.
"""

import os
import json
import glob
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, logger
from meditation_tts.config.constants import AUDIO_OUTPUT_DIR, JSON_OUTPUT_DIR, SOUNDSCAPE_DIR
from src.ffmpeg_mixer import process_meditation_audio

def find_background_file(soundscape_dir: str, soundscape_type: str) -> Optional[str]:
    """
    Find a background soundscape file matching the type, or pick a random one.
    
    Args:
        soundscape_dir: Directory containing soundscape files
        soundscape_type: Type of soundscape to find
        
    Returns:
        str or None: Path to the selected soundscape file or None if not found
    """
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
    """
    Mix generated audio with background soundscape using ffmpeg mixer.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with final audio output
    """
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