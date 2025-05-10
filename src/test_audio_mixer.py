#!/usr/bin/env python3
"""
Test script for the audio mixer module.

This script demonstrates how to use the audio_mixer module to merge
meditation voice audio with background soundscapes.
"""

import os
import sys
from pathlib import Path
import argparse

# Add the parent directory to the path so we can import the audio_mixer module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.audio_mixer import process_meditation_audio, PYDUB_AVAILABLE, check_ffmpeg_installed

def check_requirements():
    """Check if all requirements are met."""
    if not PYDUB_AVAILABLE:
        print("ERROR: pydub is not installed. Install with 'pip install pydub'")
        return False
    
    if not check_ffmpeg_installed():
        print("ERROR: ffmpeg is not installed.")
        print("Install with 'brew install ffmpeg' on macOS or follow instructions at https://ffmpeg.org/download.html")
        return False
    
    return True

def create_directories():
    """Create necessary directories if they don't exist."""
    # Create directories relative to the script location
    script_dir = Path(__file__).parent.parent
    
    output_dir = script_dir / "output"
    soundscapes_dir = script_dir / "soundscapes"
    
    if not output_dir.exists():
        print(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    if not soundscapes_dir.exists():
        print(f"Creating soundscapes directory: {soundscapes_dir}")
        soundscapes_dir.mkdir(parents=True, exist_ok=True)
        print(f"Please add some .mp3 soundscape files to {soundscapes_dir}")
    
    return str(output_dir), str(soundscapes_dir)

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description="Test the audio mixer for meditation soundscapes")
    parser.add_argument("--voice", "-v", help="Path to voice meditation audio file")
    parser.add_argument("--soundscape_dir", "-s", help="Directory containing soundscape files")
    parser.add_argument("--soundscape_type", "-t", default="nature", 
                        help="Type of soundscape to use (nature, rain, ocean, etc.)")
    parser.add_argument("--soundscape_file", "-f", 
                        help="Direct path to soundscape file (overrides soundscape_type)")
    parser.add_argument("--output_dir", "-o", help="Directory to save output files")
    
    args = parser.parse_args()
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Create directories if needed
    default_output_dir, default_soundscapes_dir = create_directories()
    
    # Use provided paths or defaults
    output_dir = args.output_dir or default_output_dir
    soundscapes_dir = args.soundscape_dir or default_soundscapes_dir
    
    # If no voice file is provided, look for one in the output directory
    voice_file = args.voice
    if not voice_file:
        # Try to find a meditation audio file in the output directory
        output_path = Path(output_dir)
        voice_files = list(output_path.glob("*.mp3"))
        
        if not voice_files:
            print("No voice file provided and no .mp3 files found in the output directory.")
            print("Please provide a voice file with the --voice option or add .mp3 files to the output directory.")
            return 1
        
        # Use the first file found
        voice_file = str(voice_files[0])
        print(f"Using {voice_file} as the voice file.")
    
    # Process the meditation audio
    full_path, sample_path = process_meditation_audio(
        voice_file=voice_file,
        soundscape_dir=soundscapes_dir,
        soundscape_type=args.soundscape_type,
        output_dir=output_dir,
        soundscape_file=args.soundscape_file
    )
    
    if full_path:
        print(f"\nSuccess! Created merged meditation audio:")
        print(f"Full audio: {full_path}")
        print(f"Sample preview: {sample_path}")
        return 0
    else:
        print("Failed to create merged meditation audio. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 