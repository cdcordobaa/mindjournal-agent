#!/usr/bin/env python
"""
Runner script for MindJournal Agent - Advanced Prosody System
"""

import os
import json
import argparse
import datetime
from dotenv import load_dotenv
from src.main import run_prosody_generation, create_test_request, EmotionalState, MeditationStyle, MeditationTheme, VoiceType, SoundscapeType

def main():
    # Load environment variables
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate a meditation script with prosody control')
    parser.add_argument('--emotional-state', type=str, choices=[e.value for e in EmotionalState], 
                        default=EmotionalState.ANXIOUS.value, help='Emotional state of the user')
    parser.add_argument('--meditation-style', type=str, choices=[s.value for s in MeditationStyle], 
                        default=MeditationStyle.MINDFULNESS.value, help='Style of meditation')
    parser.add_argument('--meditation-theme', type=str, choices=[t.value for t in MeditationTheme], 
                        default=MeditationTheme.STRESS_RELIEF.value, help='Theme of meditation')
    parser.add_argument('--duration', type=int, default=10, help='Duration in minutes')
    parser.add_argument('--voice-type', type=str, choices=[v.value for v in VoiceType], 
                        default=VoiceType.FEMALE.value, help='Type of voice')
    parser.add_argument('--language', type=str, default='es-ES', help='Language code (e.g., es-ES, en-US)')
    parser.add_argument('--soundscape', type=str, choices=[s.value for s in SoundscapeType], 
                        default=SoundscapeType.NATURE.value, help='Type of background sounds')
    parser.add_argument('--output', type=str, default='', help='Output file path (default: auto-generated in output directory)')
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key or set it manually.")
        exit(1)
    
    # Create request data from arguments or use defaults
    if args.emotional_state or args.meditation_style or args.meditation_theme or args.duration or args.voice_type or args.language or args.soundscape:
        request_data = {
            "emotional_state": args.emotional_state,
            "meditation_style": args.meditation_style,
            "meditation_theme": args.meditation_theme,
            "duration_minutes": args.duration,
            "voice_type": args.voice_type,
            "language_code": args.language,
            "soundscape": args.soundscape
        }
        print(f"Using custom parameters: {json.dumps(request_data, indent=2)}")
    else:
        request_data = create_test_request()
        print(f"Using default test parameters: {json.dumps(request_data, indent=2)}")
    
    # Run prosody generation
    print("\nRunning prosody generation...")
    result = run_prosody_generation(request_data)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Generate output filename with timestamp if not specified
    if not args.output:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/meditation_{request_data['emotional_state']}_{request_data['meditation_theme']}_{timestamp}.json"
    else:
        output_path = args.output
    
    # Save output
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nOutput saved to {output_path}")
    
    # Display summary
    if result.get("error"):
        print(f"\nError: {result['error']}")
    else:
        print("\nGeneration completed successfully!")
        print("\nGenerated Meditation Script (excerpt):")
        print("----------------------------")
        content = result["meditation_script"]["content"]
        print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    main() 