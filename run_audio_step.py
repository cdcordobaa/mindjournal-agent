#!/usr/bin/env python
"""
Runner script for the Meditation TTS System that lets you start from specific workflow steps.
Particularly useful for re-running the audio generation step after fixing issues.
"""

import os
import sys
import argparse
import json
import glob
import random
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from meditation_tts.workflow.runner import run_meditation_generation
from meditation_tts.utils.logging_utils import logger
from meditation_tts.config.constants import WORKFLOW_STEPS, STATE_DIR, JSON_OUTPUT_DIR, AUDIO_OUTPUT_DIR, SOUNDSCAPE_DIR
from src.ffmpeg_mixer import process_meditation_audio, check_ffmpeg_installed

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

def load_state(filepath: str) -> Optional[Dict[str, Any]]:
    """Load state from a JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state from {filepath}: {str(e)}")
        return None

def mix_audio_directly(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mix the generated voice audio with a background soundscape.
    
    Args:
        state: Current workflow state with audio_output.voice_file
    
    Returns:
        Updated state with mixed audio information
    """
    try:
        print("Mixing audio with background soundscape...")
        
        if not state.get("audio_output", {}).get("voice_file"):
            print("Error: No voice file found in state")
            state["error"] = "No voice file to mix"
            return state
        
        # Check if ffmpeg is installed
        if not check_ffmpeg_installed():
            print("Error: ffmpeg is not installed. Please install it to mix audio.")
            state["error"] = "ffmpeg is not installed"
            return state
        
        # Find a background soundscape file
        soundscape_type = state["request"].get("soundscape", "nature")
        background_file = find_background_file(SOUNDSCAPE_DIR, soundscape_type)
        
        if not background_file:
            print(f"Error: No suitable soundscape file found for type: {soundscape_type}")
            print(f"Please make sure you have .mp3 files in the {SOUNDSCAPE_DIR} directory")
            state["error"] = f"No suitable soundscape file found for type: {soundscape_type}"
            return state
        
        print(f"Using soundscape file: {background_file}")
        
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
            
            print(f"Mixed audio successfully:")
            print(f"  Full audio: {full_audio}")
            if sample_audio:
                print(f"  Sample: {sample_audio}")
            
            # Save the complete state to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_output = {
                "request": state["request"],
                "meditation_script": state.get("meditation_script"),
                "prosody_analysis": state.get("prosody_analysis"),
                "prosody_profile": state.get("prosody_profile"),
                "audio_output": state["audio_output"]
            }
            
            json_file = os.path.join(JSON_OUTPUT_DIR, f"meditation_{timestamp}.json")
            os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
            
            with open(json_file, 'w') as f:
                json.dump(json_output, f, indent=2)
                
            state["audio_output"]["json_file"] = json_file
            print(f"Saved complete state to JSON: {json_file}")
        else:
            print("Error: Failed to mix audio with soundscape")
            state["error"] = "Failed to mix audio with soundscape"
        
        return state
        
    except Exception as e:
        import traceback
        print(f"Error mixing audio: {str(e)}")
        print(traceback.format_exc())
        state["error"] = f"Error mixing audio: {str(e)}"
        return state

def run_from_step(step: str, state_file: Optional[str] = None, end_step: Optional[str] = None, reduced_ssml: bool = False):
    """
    Run the meditation workflow from a specific step.
    
    Args:
        step: The workflow step to start from
        state_file: Optional path to a specific state file
        end_step: Optional step to end at
        reduced_ssml: If True, reduce SSML complexity to avoid length issues
    """
    if step not in WORKFLOW_STEPS:
        print(f"Error: '{step}' is not a valid workflow step.")
        print(f"Valid steps are: {', '.join(WORKFLOW_STEPS)}")
        return
    
    # Find and load the appropriate state file
    if state_file:
        state_path = state_file
    else:
        # Find the latest state from the previous step
        prev_step_idx = WORKFLOW_STEPS.index(step) - 1
        if prev_step_idx >= 0:
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            state_path = get_latest_state_file(prev_step)
        else:
            print(f"Cannot run from {step} without a previous state. Please provide a state file.")
            return
    
    if not state_path or not os.path.exists(state_path):
        print(f"Error: State file not found.")
        return
    
    # Load the state
    state = load_state(state_path)
    if not state:
        print(f"Error: Failed to load state from {state_path}")
        return
    
    print(f"Loaded state from: {state_path}")
    
    # If we're running from the audio generation step and reduced_ssml is True, simplify the SSML
    if step == "generate_audio" and reduced_ssml and "ssml_output" in state:
        print("Simplifying SSML to reduce length...")
        import re
        from bs4 import BeautifulSoup
        
        try:
            # Parse and simplify the SSML
            ssml = state["ssml_output"]
            soup = BeautifulSoup(ssml, 'xml')
            
            # Remove nested prosody tags (keep only the innermost one)
            nested_prosody = soup.find_all('prosody', recursive=True)
            for prosody in nested_prosody:
                inner_prosody = prosody.find_all('prosody', recursive=True)
                for inner in inner_prosody:
                    # Replace the inner prosody tag with its contents
                    inner.replace_with(inner.get_text())
            
            # Update the state with the simplified SSML
            state["ssml_output"] = str(soup)
            print(f"SSML simplified: {len(state['ssml_output'])} characters")
        except Exception as e:
            print(f"Warning: Could not simplify SSML: {str(e)}")
    
    # Update the current step in the state
    state["current_step"] = step
    state["error"] = None  # Clear any previous errors
    
    # Import node functions directly to avoid LangGraph execution issues
    from meditation_tts.workflow.nodes import (
        generate_meditation_script,
        analyze_prosody_needs,
        generate_prosody_profile,
        generate_ssml,
        review_and_improve_ssml,
        generate_meditation_audio,
        mix_with_soundscape
    )
    
    # Map steps to functions
    step_functions = {
        "generate_script": generate_meditation_script,
        "analyze_prosody": analyze_prosody_needs,
        "create_profile": generate_prosody_profile,
        "generate_ssml": generate_ssml,
        "review_and_improve_ssml": review_and_improve_ssml,
        "generate_audio": generate_meditation_audio,
        "mix_audio": mix_with_soundscape
    }
    
    # Determine which steps to run
    start_idx = WORKFLOW_STEPS.index(step)
    end_idx = WORKFLOW_STEPS.index(end_step) if end_step in WORKFLOW_STEPS else len(WORKFLOW_STEPS) - 1
    steps_to_run = WORKFLOW_STEPS[start_idx:end_idx + 1]
    
    print(f"Running the following steps: {', '.join(steps_to_run)}")
    
    result = state
    # Run each step directly
    for current_step in steps_to_run:
        print(f"\nRunning step: {current_step}")
        step_function = step_functions.get(current_step)
        
        if not step_function:
            print(f"Error: No function found for step '{current_step}'")
            result["error"] = f"No function found for step '{current_step}'"
            break
        
        try:
            # Special case for mix_audio - use our direct implementation instead
            if current_step == "mix_audio":
                print("Using direct audio mixing implementation...")
                result = mix_audio_directly(result)
            else:
                result = step_function(result)
            
            # Save state after each step
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            state_output_path = os.path.join(STATE_DIR, f"state_{current_step}_{timestamp}.json")
            os.makedirs(os.path.dirname(state_output_path), exist_ok=True)
            
            with open(state_output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"Saved state to: {state_output_path}")
            
            # Check for errors
            if result.get("error"):
                print(f"Error in step {current_step}: {result['error']}")
                break
                
        except Exception as e:
            import traceback
            print(f"Exception in step {current_step}: {str(e)}")
            print(traceback.format_exc())
            result["error"] = f"Exception in step {current_step}: {str(e)}"
            break
    
    # Ensure audio mixing happens if we just generated audio
    if step == "generate_audio" and "mix_audio" not in steps_to_run and not result.get("error") and result.get("audio_output", {}).get("voice_file"):
        print("\nAuto-running audio mixing step after successful audio generation...")
        result = mix_audio_directly(result)
    
    # Display results
    if result.get("error"):
        print(f"\nError: {result['error']}")
    else:
        print("\nGeneration completed successfully!")
        if result.get("audio_output"):
            if result["audio_output"].get("full_audio"):
                print(f"\nGenerated mixed audio file: {result['audio_output'].get('full_audio', 'Unknown')}")
            else:
                print(f"\nGenerated voice file: {result['audio_output'].get('voice_file', 'Unknown')}")
        if result.get("meditation_script"):
            print("\nMeditation script is available in the state.")
    
    return result

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

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(description='Run the meditation workflow from a specific step')
    parser.add_argument('--step', type=str, default="generate_audio",
                      help=f'Step to start from (default: generate_audio). Options: {", ".join(WORKFLOW_STEPS)}')
    parser.add_argument('--state-file', type=str, 
                      help='Path to a specific state file to use (optional)')
    parser.add_argument('--end-step', type=str,
                      help='Step to end at (optional)')
    parser.add_argument('--reduce-ssml', action='store_true',
                      help='Simplify SSML to reduce length (useful for audio generation)')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key or set it manually.")
        exit(1)
    
    # Create output directories
    os.makedirs("output/audio", exist_ok=True)
    os.makedirs("output/state", exist_ok=True)
    
    # Run the workflow from the specified step
    run_from_step(args.step, args.state_file, args.end_step, args.reduce_ssml)

if __name__ == "__main__":
    main() 