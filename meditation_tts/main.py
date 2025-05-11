"""
Main entry point for the meditation TTS system.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from meditation_tts.models.enums import (
    EmotionalState,
    MeditationStyle,
    MeditationTheme,
    VoiceType,
    SoundscapeType
)
from meditation_tts.workflow.runner import run_meditation_generation
from meditation_tts.utils.logging_utils import logger

def create_test_request() -> Dict[str, Any]:
    """
    Create a test request with default parameters.
    
    Returns:
        Dict[str, Any]: A default request configuration
    """
    return {
        "emotional_state": EmotionalState.ANXIOUS.value,
        "meditation_style": MeditationStyle.MINDFULNESS.value,
        "meditation_theme": MeditationTheme.STRESS_RELIEF.value,
        "duration_minutes": 10,
        "voice_type": VoiceType.FEMALE.value,
        "language_code": "en-US",
        "soundscape": SoundscapeType.NATURE.value
    }

def run_prosody_generation(request_data: Dict[str, Any], start_step: Optional[str] = None, end_step: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the prosody generation workflow.
    
    Args:
        request_data: Request data for the meditation generation
        start_step: Optional step to start from
        end_step: Optional step to end at
        
    Returns:
        Dict[str, Any]: The result state after workflow completion
    """
    logger.info(f"Starting prosody generation with request: {json.dumps(request_data)}")
    return run_meditation_generation(request_data, start_step, end_step)

def main():
    """Main function for console script."""
    import argparse
    
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
    parser.add_argument('--language', type=str, default='en-US', help='Language code (e.g., es-ES, en-US)')
    parser.add_argument('--soundscape', type=str, choices=[s.value for s in SoundscapeType], 
                      default=SoundscapeType.NATURE.value, help='Type of background sounds')
    parser.add_argument('--output', type=str, default='', help='Output file path (default: auto-generated in output directory)')
    parser.add_argument('--start-step', type=str, default=None, help='Start from a specific workflow step')
    parser.add_argument('--end-step', type=str, default=None, help='End at a specific workflow step')
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key or set it manually.")
        exit(1)
    
    # Create request data from arguments or use defaults
    request_data = {
        "emotional_state": args.emotional_state,
        "meditation_style": args.meditation_style,
        "meditation_theme": args.meditation_theme,
        "duration_minutes": args.duration,
        "voice_type": args.voice_type,
        "language_code": args.language,
        "soundscape": args.soundscape
    }
    
    # Run prosody generation
    print("\nRunning prosody generation...")
    result = run_prosody_generation(request_data, args.start_step, args.end_step)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Generate output filename with timestamp if not specified
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        if result.get("meditation_script"):
            print("\nGenerated Meditation Script (excerpt):")
            print("----------------------------")
            content = result["meditation_script"]["content"]
            print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    main()
