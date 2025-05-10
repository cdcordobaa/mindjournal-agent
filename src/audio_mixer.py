"""
Audio Mixer for Meditation Soundscapes

This module handles the process of merging meditation voice audio with 
background soundscapes to create the final meditation audio experience.
"""

import os
import random
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('audio_mixer')

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    logger.warning("pydub not available. Install with 'pip install pydub'")
    PYDUB_AVAILABLE = False


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


def get_audio_info(file_path: str) -> Tuple[float, int]:
    """Get information about the audio file using ffprobe.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Tuple of (duration in seconds, bit rate)
    """
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration,bit_rate', '-of',
            'default=noprint_wrappers=1:nokey=1', file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        output = result.stdout.strip().split('\n')
        if len(output) >= 2:
            duration, bit_rate = output
            return float(duration), int(bit_rate)
        else:
            # Sometimes bit_rate isn't available
            duration = output[0]
            return float(duration), 0
    except Exception as e:
        logger.error(f"Error getting audio info for {file_path}: {str(e)}")
        return 0.0, 0


def list_available_soundscapes(soundscape_dir: str) -> Dict[str, List[str]]:
    """List all available soundscape files grouped by type.
    
    Args:
        soundscape_dir: Directory containing soundscape files
        
    Returns:
        Dictionary of soundscape types to lists of file paths
    """
    if not os.path.exists(soundscape_dir):
        logger.warning(f"Soundscape directory '{soundscape_dir}' does not exist")
        return {}
    
    soundscapes = {}
    
    # Common soundscape types and their keywords
    type_keywords = {
        "nature": ["nature", "forest", "birds", "river", "stream", "wind"],
        "rain": ["rain", "thunder", "storm"],
        "ocean": ["ocean", "waves", "sea", "beach"],
        "ambient": ["ambient", "background", "atmosphere"],
        "urban": ["urban", "city", "coffee", "cafe"],
        "silence": ["silence"],
        "night": ["night", "crickets", "evening"]
    }
    
    for file in os.listdir(soundscape_dir):
        if not file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
            continue
            
        file_path = os.path.join(soundscape_dir, file)
        file_lower = file.lower()
        
        # Determine the type based on filename
        matched_type = None
        for type_name, keywords in type_keywords.items():
            if any(keyword in file_lower for keyword in keywords):
                matched_type = type_name
                break
        
        if matched_type is None:
            matched_type = "other"
            
        if matched_type not in soundscapes:
            soundscapes[matched_type] = []
            
        soundscapes[matched_type].append(file_path)
    
    return soundscapes


def select_soundscape(soundscape_dir: str, soundscape_type: str) -> Optional[str]:
    """Select an appropriate soundscape file based on type.
    
    Args:
        soundscape_dir: Directory containing soundscape files
        soundscape_type: Type of soundscape to select
        
    Returns:
        Path to selected soundscape file or None if not found
    """
    soundscapes = list_available_soundscapes(soundscape_dir)
    
    # Normalize the soundscape type
    soundscape_type = soundscape_type.lower()
    
    # Map SoundscapeType enum values to actual directory categories
    type_mapping = {
        "nature": "nature",
        "urban": "urban",
        "ambient": "ambient",
        "silence": "silence",
        "rain": "rain",
        "ocean": "ocean",
        "forest": "nature",
        "nighttime": "night"
    }
    
    mapped_type = type_mapping.get(soundscape_type, soundscape_type)
    
    if mapped_type in soundscapes and soundscapes[mapped_type]:
        # Randomly select one from the appropriate category
        return random.choice(soundscapes[mapped_type])
    
    # If specific type not found, try to find any suitable audio
    all_files = []
    for files in soundscapes.values():
        all_files.extend(files)
    
    if all_files:
        logger.warning(f"Soundscape type '{soundscape_type}' not found, selecting random soundscape")
        return random.choice(all_files)
    
    logger.error(f"No soundscape files found in '{soundscape_dir}'")
    return None


def merge_audio(
    voice_file: str, 
    background_file: str, 
    output_file: str, 
    background_volume_reduction: int = 15,
    create_sample: bool = True,
    sample_duration: int = 30
) -> Tuple[Optional[str], Optional[str]]:
    """Merge voice audio with background soundscape.
    
    Args:
        voice_file: Path to voice meditation audio file
        background_file: Path to background soundscape file
        output_file: Path to save the merged audio
        background_volume_reduction: How many dB to reduce background volume
        create_sample: Whether to create a short sample for preview
        sample_duration: Duration of sample in seconds
        
    Returns:
        Tuple of (path to full merged audio, path to sample) or (None, None) on error
    """
    if not PYDUB_AVAILABLE:
        logger.error("Cannot merge audio: pydub is not installed")
        return None, None
        
    if not check_ffmpeg_installed():
        logger.error("Cannot merge audio: ffmpeg is not installed")
        return None, None
    
    try:
        # Get info about the files
        voice_duration, voice_bitrate = get_audio_info(voice_file)
        bg_duration, bg_bitrate = get_audio_info(background_file)
        
        logger.info(f"Voice file: duration={voice_duration:.2f}s, bitrate={voice_bitrate}bps")
        logger.info(f"Background file: duration={bg_duration:.2f}s, bitrate={bg_bitrate}bps")

        # Load audio files
        voice = AudioSegment.from_file(voice_file)
        background = AudioSegment.from_file(background_file)

        voice_duration_ms = len(voice)
        background_duration_ms = len(background)

        logger.info(f"Loaded voice duration: {voice_duration_ms/1000:.2f}s")
        logger.info(f"Loaded background duration: {background_duration_ms/1000:.2f}s")

        # If background is longer than voice, select a random segment
        if background_duration_ms > voice_duration_ms:
            start_point = random.randint(0, background_duration_ms - voice_duration_ms)
            background = background[start_point:start_point + voice_duration_ms]
        else:
            # If background is shorter, loop it to match voice length
            loops_needed = voice_duration_ms // background_duration_ms + 1
            background = background * loops_needed
            background = background[:voice_duration_ms]

        # Reduce volume of background
        background = background - background_volume_reduction  # Reduce by specified dB

        # Apply fade in and out
        fade_duration = min(3000, voice_duration_ms // 10)  # 3 sec or 10% of total, whichever is less
        background = background.fade_in(fade_duration).fade_out(fade_duration)

        # Overlay voice on background
        output = background.overlay(voice)

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the result
        output.export(output_file, format="mp3")
        logger.info(f"Merged audio saved as {output_file}")

        sample_file = None
        if create_sample:
            # Create a sample from a random section
            sample_duration_ms = min(sample_duration * 1000, len(output))
            sample_start = random.randint(0, max(0, len(output) - sample_duration_ms))
            sample = output[sample_start:sample_start + sample_duration_ms]
            
            # Use same directory but prefix filename with 'sample_'
            output_basename = os.path.basename(output_file)
            sample_file = os.path.join(output_dir, f"sample_{output_basename}")
            
            sample.export(sample_file, format="mp3")
            logger.info(f"Sample audio saved as {sample_file}")

        return output_file, sample_file

    except Exception as e:
        logger.error(f"An error occurred during audio merging: {str(e)}")
        return None, None


def process_meditation_audio(
    voice_file: str,
    soundscape_dir: str,
    soundscape_type: str = "nature",
    output_dir: str = "output",
    create_sample: bool = True,
    soundscape_file: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Process a meditation audio file by merging it with an appropriate soundscape.
    
    Args:
        voice_file: Path to voice meditation audio file
        soundscape_dir: Directory containing soundscape files
        soundscape_type: Type of soundscape to use (ignored if soundscape_file is provided)
        output_dir: Directory to save output files
        create_sample: Whether to create a sample preview
        soundscape_file: Direct path to soundscape file to use (overrides soundscape_type)
        
    Returns:
        Tuple of (path to full merged audio, path to sample) or (None, None) on error
    """
    try:
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            logger.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)
            
        # Check if voice file exists
        if not os.path.exists(voice_file):
            logger.error(f"Voice file not found: {voice_file}")
            return None, None
        
        # Get the background file
        background_file = None
        
        if soundscape_file:
            # Use the directly specified soundscape file
            if os.path.exists(soundscape_file):
                background_file = soundscape_file
                logger.info(f"Using directly specified soundscape file: {background_file}")
            else:
                logger.error(f"Specified soundscape file not found: {soundscape_file}")
                return None, None
        else:
            # Select appropriate soundscape by type
            background_file = select_soundscape(soundscape_dir, soundscape_type)
            if not background_file:
                logger.error(f"No suitable soundscape found for type: {soundscape_type}")
                return None, None
            
        # Generate output filename based on input
        voice_basename = os.path.basename(voice_file)
        voice_name = os.path.splitext(voice_basename)[0]
        background_name = os.path.splitext(os.path.basename(background_file))[0]
        output_filename = f"{voice_name}_with_{background_name}.mp3"
        output_file = os.path.join(output_dir, output_filename)
        
        # Merge the audio files
        return merge_audio(
            voice_file=voice_file,
            background_file=background_file,
            output_file=output_file,
            create_sample=create_sample
        )
        
    except Exception as e:
        logger.error(f"Error processing meditation audio: {str(e)}")
        return None, None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge meditation voice with background soundscapes")
    parser.add_argument("--voice", "-v", required=True, help="Path to voice meditation audio file")
    parser.add_argument("--soundscape_dir", "-s", default="./soundscapes", help="Directory containing soundscape files")
    parser.add_argument("--soundscape_type", "-t", default="nature", help="Type of soundscape to use")
    parser.add_argument("--soundscape_file", "-f", help="Direct path to soundscape file (overrides soundscape_type)")
    parser.add_argument("--output_dir", "-o", default="./output", help="Directory to save output files")
    parser.add_argument("--no_sample", action="store_true", help="Don't create a sample preview")
    
    args = parser.parse_args()
    
    # Check requirements first
    if not PYDUB_AVAILABLE:
        print("\nERROR: pydub is not installed. Installing it now...")
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pydub"], check=True)
            print("pydub installed successfully, trying to import it now")
            try:
                from pydub import AudioSegment
                PYDUB_AVAILABLE = True
                print("pydub imported successfully after installation")
            except ImportError as e:
                print(f"Failed to import pydub after installation: {e}")
                print("You may need to install additional dependencies:")
                print("  - For MacOS: brew install portaudio")
                print("  - For Linux: apt-get install python3-pyaudio")
                print("  - For Windows: pip install pyaudio")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to install pydub: {e}")
            sys.exit(1)
    
    if not check_ffmpeg_installed():
        print("\nERROR: ffmpeg is not installed.")
        if sys.platform == 'darwin':
            print("Install with: brew install ffmpeg")
        elif sys.platform.startswith('linux'):
            print("Install with: apt-get install ffmpeg")
        else:
            print("Download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Now run the audio processing
    full_path, sample_path = process_meditation_audio(
        voice_file=args.voice,
        soundscape_dir=args.soundscape_dir,
        soundscape_type=args.soundscape_type,
        output_dir=args.output_dir,
        create_sample=not args.no_sample,
        soundscape_file=args.soundscape_file
    )
    
    if full_path:
        print(f"\nFull meditation audio: {full_path}")
        if sample_path:
            print(f"Sample audio for preview: {sample_path}")
    else:
        print("Failed to process meditation audio. Check logs for details.") 