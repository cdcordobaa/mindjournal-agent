"""
Integration module for connecting audio mixer with LangGraph workflow.

This module provides functions to integrate the audio mixer with the existing
meditation generation system using LangGraph.
"""

import os
import json
import datetime
from typing import Dict, Optional, Tuple, Any

from src.audio_mixer import process_meditation_audio


def post_process_meditation_audio(
    state_result: Dict[str, Any],
    voice_file: str,
    soundscape_dir: str = "soundscapes",
    output_dir: str = "output",
    soundscape_file: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Post-process a meditation audio by adding appropriate soundscapes.
    
    Args:
        state_result: The result from the LangGraph workflow execution
        voice_file: Path to the generated voice audio file from Polly
        soundscape_dir: Directory containing soundscape files
        output_dir: Directory to save output files
        soundscape_file: Direct path to soundscape file (overrides soundscape_type)
        
    Returns:
        Tuple of (path to full merged audio, path to sample) or (None, None) on error
    """
    try:
        # Extract soundscape type from the state result
        request = state_result.get("request", {})
        soundscape_type = request.get("soundscape", "nature")
        
        # Process the meditation audio with the appropriate soundscape
        return process_meditation_audio(
            voice_file=voice_file,
            soundscape_dir=soundscape_dir,
            soundscape_type=soundscape_type,
            output_dir=output_dir,
            soundscape_file=soundscape_file
        )
        
    except Exception as e:
        print(f"Error post-processing meditation audio: {str(e)}")
        return None, None


def extend_workflow(workflow):
    """
    Extend the existing LangGraph workflow to include audio mixing.
    
    NOTE: This is a placeholder for future integration with the 
    LangGraph workflow. It doesn't modify the workflow yet.
    
    Args:
        workflow: The LangGraph workflow to extend
        
    Returns:
        The extended workflow
    """
    # This is a placeholder function - we'll implement integration later
    return workflow


def create_meditation_with_soundscape(
    request_data: Dict[str, Any],
    voice_file: str,
    soundscape_dir: str = "soundscapes",
    output_dir: str = "output",
    soundscape_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a complete meditation with voice and soundscape in one step.
    
    This function demonstrates how to use the flow from prosody generation
    to final audio with soundscape, but doesn't implement the full integration yet.
    
    Args:
        request_data: The request data for the LangGraph workflow
        voice_file: Path to the generated voice audio file
        soundscape_dir: Directory containing soundscape files
        output_dir: Directory to save output files
        soundscape_file: Direct path to soundscape file (overrides soundscape_type)
        
    Returns:
        Dictionary with results of the meditation creation
    """
    # For demonstration only - this would normally involve the actual workflow
    result = {
        "request": request_data,
        "meditation_script": {
            "content": "This is a placeholder for the meditation script content."
        },
        "prosody_analysis": None,
        "prosody_profile": None,
        "ssml_output": None,
        "error": None
    }
    
    # Process the audio with soundscape
    full_audio, sample_audio = process_meditation_audio(
        voice_file=voice_file,
        soundscape_dir=soundscape_dir,
        soundscape_type=request_data.get("soundscape", "nature"),
        output_dir=output_dir,
        soundscape_file=soundscape_file
    )
    
    # Add audio results to the result dictionary
    used_soundscape = soundscape_file if soundscape_file else f"auto-selected ({request_data.get('soundscape', 'nature')} type)"
    
    result["audio_output"] = {
        "voice_file": voice_file,
        "full_audio": full_audio,
        "sample_audio": sample_audio,
        "soundscape": used_soundscape,
        "processing_time": datetime.datetime.now().isoformat()
    }
    
    return result


if __name__ == "__main__":
    # This is just an example of how to use the module
    print("This module is meant to be imported, not run directly.")
    print("It provides integration functions for connecting the audio mixer")
    print("with the LangGraph meditation generation workflow.") 