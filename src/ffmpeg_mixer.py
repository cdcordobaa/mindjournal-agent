#!/usr/bin/env python3
"""
FFmpeg-based Audio Mixer for Meditation Soundscapes

This is a simplified version that uses ffmpeg directly through subprocess
instead of relying on pydub. This is useful when pydub installation is problematic.
"""

import os
import sys
import random
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ffmpeg_mixer')

def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        return True
    except FileNotFoundError:
        logger.error("ffmpeg not found. Install it with 'brew install ffmpeg' on macOS or "
                     "follow instructions at https://ffmpeg.org/download.html")
        return False

def create_output_dir(output_dir: str) -> bool:
    """Create output directory if it doesn't exist."""
    if not os.path.exists(output_dir):
        logger.info(f"Creating output directory: {output_dir}")
        try:
            os.makedirs(output_dir)
            return True
        except Exception as e:
            logger.error(f"Error creating output directory: {str(e)}")
            return False
    return True

def merge_audio_with_ffmpeg(
    voice_file: str,
    background_file: str,
    output_file: str,
    background_volume: float = 0.3,  # 0.0 to 1.0
    create_sample: bool = True,
    sample_duration: int = 30
) -> Tuple[Optional[str], Optional[str]]:
    """
    Merge voice audio with background soundscape using ffmpeg directly.
    
    Args:
        voice_file: Path to voice meditation audio file
        background_file: Path to background soundscape file
        output_file: Path to save the merged audio
        background_volume: Volume of background (0.0 to 1.0)
        create_sample: Whether to create a short sample for preview
        sample_duration: Duration of sample in seconds
        
    Returns:
        Tuple of (path to full merged audio, path to sample) or (None, None) on error
    """
    try:
        if not check_ffmpeg_installed():
            logger.error("Cannot merge audio: ffmpeg is not installed")
            return None, None
            
        # Check if files exist
        if not os.path.exists(voice_file):
            logger.error(f"Voice file not found: {voice_file}")
            return None, None
            
        if not os.path.exists(background_file):
            logger.error(f"Background file not found: {background_file}")
            return None, None
            
        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Get duration of voice file for looping background if needed
        voice_duration_cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            voice_file
        ]
        voice_duration_result = subprocess.run(
            voice_duration_cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        voice_duration = float(voice_duration_result.stdout.strip())
        
        # Get duration of background file
        bg_duration_cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            background_file
        ]
        bg_duration_result = subprocess.run(
            bg_duration_cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        bg_duration = float(bg_duration_result.stdout.strip())
        
        logger.info(f"Voice duration: {voice_duration:.2f}s")
        logger.info(f"Background duration: {bg_duration:.2f}s")
        
        # Determine filter_complex arguments based on durations
        filter_complex = ""
        
        if bg_duration >= voice_duration:
            # If background is longer, just trim it
            random_start = random.uniform(0, max(0, bg_duration - voice_duration))
            filter_complex = (
                f"[1:a]atrim=start={random_start}:duration={voice_duration},"
                f"asetpts=PTS-STARTPTS,volume={background_volume}[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first"
            )
        else:
            # If background is shorter, loop it
            loops_needed = int(voice_duration / bg_duration) + 1
            filter_complex = (
                f"[1:a]aloop=loop={loops_needed}:size={int(bg_duration*44100)},"
                f"atrim=duration={voice_duration},asetpts=PTS-STARTPTS,"
                f"volume={background_volume}[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first"
            )
            
        # Run ffmpeg command to merge audio
        merge_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', voice_file,
            '-i', background_file,
            '-filter_complex', filter_complex,
            '-codec:a', 'libmp3lame',
            '-q:a', '2',
            output_file
        ]
        
        logger.info(f"Running ffmpeg command to merge audio files")
        subprocess.run(merge_cmd, check=True)
        logger.info(f"Merged audio saved as {output_file}")
        
        # Create sample if requested
        sample_file = None
        if create_sample:
            # Create output path for sample
            output_base = os.path.basename(output_file)
            sample_file = os.path.join(output_dir, f"sample_{output_base}")
            
            # Determine sample start time (random within the first 2/3 of the file)
            max_start_time = max(0, voice_duration - sample_duration)
            if max_start_time > 10:  # If file is long enough, don't start at the very beginning
                sample_start = random.uniform(10, max_start_time)
            else:
                sample_start = 0
                
            # Create sample with ffmpeg
            sample_cmd = [
                'ffmpeg',
                '-y',
                '-i', output_file,
                '-ss', f"{sample_start}",
                '-t', f"{sample_duration}",
                '-acodec', 'copy',
                sample_file
            ]
            
            logger.info(f"Creating sample from {sample_start:.2f}s to {sample_start+sample_duration:.2f}s")
            subprocess.run(sample_cmd, check=True)
            logger.info(f"Sample audio saved as {sample_file}")
            
        return output_file, sample_file
        
    except Exception as e:
        logger.error(f"Error merging audio: {str(e)}")
        return None, None

def process_meditation_audio(
    voice_file: str,
    background_file: str,
    output_dir: str = "output",
    background_volume: float = 0.3,
    create_sample: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """
    Process a meditation audio file by merging it with a soundscape.
    
    Args:
        voice_file: Path to voice meditation audio file
        background_file: Path to background soundscape file
        output_dir: Directory to save output files
        background_volume: Volume of background (0.0 to 1.0)
        create_sample: Whether to create a sample preview
        
    Returns:
        Tuple of (path to full merged audio, path to sample) or (None, None) on error
    """
    try:
        # Create output directory if needed
        if not create_output_dir(output_dir):
            return None, None
            
        # Generate output filename based on input
        voice_basename = os.path.basename(voice_file)
        voice_name = os.path.splitext(voice_basename)[0]
        background_name = os.path.splitext(os.path.basename(background_file))[0]
        output_filename = f"{voice_name}_with_{background_name}.mp3"
        output_file = os.path.join(output_dir, output_filename)
        
        # Merge the audio files
        return merge_audio_with_ffmpeg(
            voice_file=voice_file,
            background_file=background_file,
            output_file=output_file,
            background_volume=background_volume,
            create_sample=create_sample
        )
        
    except Exception as e:
        logger.error(f"Error processing meditation audio: {str(e)}")
        return None, None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge meditation voice with background soundscapes using FFmpeg")
    parser.add_argument("--voice", "-v", required=True, help="Path to voice meditation audio file")
    parser.add_argument("--background", "-b", required=True, help="Path to background soundscape file")
    parser.add_argument("--output_dir", "-o", default="./output", help="Directory to save output files")
    parser.add_argument("--volume", "-vol", type=float, default=0.3, help="Background volume (0.0 to 1.0)")
    parser.add_argument("--no_sample", action="store_true", help="Don't create a sample preview")
    
    args = parser.parse_args()
    
    if not check_ffmpeg_installed():
        print("\nERROR: ffmpeg is not installed.")
        if sys.platform == 'darwin':
            print("Install with: brew install ffmpeg")
        elif sys.platform.startswith('linux'):
            print("Install with: apt-get install ffmpeg")
        else:
            print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    full_path, sample_path = process_meditation_audio(
        voice_file=args.voice,
        background_file=args.background,
        output_dir=args.output_dir,
        background_volume=args.volume,
        create_sample=not args.no_sample
    )
    
    if full_path:
        print(f"\nFull meditation audio: {full_path}")
        if sample_path:
            print(f"Sample audio for preview: {sample_path}")
    else:
        print("Failed to process meditation audio. Check logs for details.") 