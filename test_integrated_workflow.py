#!/usr/bin/env python3
"""
Test script for the integrated meditation generation workflow.
"""

import os
import json
import argparse
from dotenv import load_dotenv
from src.integrated_workflow import run_meditation_generation, WORKFLOW_STEPS
from src.main import EmotionalState, MeditationStyle, MeditationTheme, VoiceType, SoundscapeType

def main():
    # Load environment variables
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test the meditation generation workflow')
    parser.add_argument('--start-step', choices=WORKFLOW_STEPS, help='Start from a specific workflow step')
    args = parser.parse_args()
    
    # Create a sample request
    request_data = {
        "emotional_state": EmotionalState.ANXIOUS.value,
        "meditation_style": MeditationStyle.MINDFULNESS.value,
        "meditation_theme": MeditationTheme.STRESS_RELIEF.value,
        "duration_minutes": 10,
        "voice_type": VoiceType.FEMALE.value,
        "language_code": "en-US",
        "soundscape": SoundscapeType.NATURE.value
    }
    
    print("Starting meditation generation...")
    print(f"Request parameters: {json.dumps(request_data, indent=2)}")
    
    if args.start_step:
        print(f"\nStarting from step: {args.start_step}")
        print("Available steps:")
        for i, step in enumerate(WORKFLOW_STEPS, 1):
            print(f"{i}. {step}")
    
    # Run the workflow
    result = run_meditation_generation(request_data, start_step=args.start_step)
    
    # Check for errors
    if result.get("error"):
        print(f"\nError occurred: {result['error']}")
        return 1
        
    # Print results
    print("\nMeditation generation completed successfully!")
    print("\nOutput files:")
    if result.get("audio_output"):
        audio_output = result["audio_output"]
        print(f"- Voice file: {audio_output.get('voice_file')}")
        print(f"- Full audio: {audio_output.get('full_audio')}")
        print(f"- Sample audio: {audio_output.get('sample_audio')}")
        print(f"- JSON output: {audio_output.get('json_file')}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 