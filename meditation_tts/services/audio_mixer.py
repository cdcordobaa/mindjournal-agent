"""
FFmpeg-based Audio Mixer for Meditation Soundscapes.
"""

import os
import sys
import random
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from meditation_tts.utils.logging_utils import logger

class AudioMixer:
    """Service for mixing voice audio with background soundscapes."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the AudioMixer.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        
    @staticmethod
    def check_ffmpeg_installed() -> bool:
        """
        Check if ffmpeg is installed on the system.
        
        Returns:
            bool: True if ffmpeg is installed, False otherwise
        """
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

    def create_output_dir(self) -> bool:
        """
        Create output directory if it doesn't exist.
        
        Returns:
            bool: True if directory exists or was created, False otherwise
        """
        if not os.path.exists(self.output_dir):
            logger.info(f"Creating output directory: {self.output_dir}")
            try:
                os.makedirs(self.output_dir)
                return True
            except Exception as e:
                logger.error(f"Error creating output directory: {str(e)}")
                return False
        return True

    def merge_audio(
        self,
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
            if not self.check_ffmpeg_installed():
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
        self,
        voice_file: str,
        background_file: str,
        background_volume: float = 0.3,
        create_sample: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a meditation audio file by merging it with a soundscape.
        
        Args:
            voice_file: Path to voice meditation audio file
            background_file: Path to background soundscape file
            background_volume: Volume of background (0.0 to 1.0)
            create_sample: Whether to create a sample preview
            
        Returns:
            Tuple of (path to full merged audio, path to sample) or (None, None) on error
        """
        try:
            # Create output directory if needed
            if not self.create_output_dir():
                return None, None
                
            # Generate output filename based on input
            voice_basename = os.path.basename(voice_file)
            voice_name = os.path.splitext(voice_basename)[0]
            background_name = os.path.splitext(os.path.basename(background_file))[0]
            output_filename = f"{voice_name}_with_{background_name}.mp3"
            output_file = os.path.join(self.output_dir, output_filename)
            
            # Merge the audio files
            return self.merge_audio(
                voice_file=voice_file,
                background_file=background_file,
                output_file=output_file,
                background_volume=background_volume,
                create_sample=create_sample
            )
            
        except Exception as e:
            logger.error(f"Error processing meditation audio: {str(e)}")
            return None, None

    @staticmethod
    def find_background_file(soundscape_dir: str, soundscape_type: str) -> Optional[str]:
        """
        Find a background soundscape file matching the type, or pick a random one.
        
        Args:
            soundscape_dir: Directory containing soundscape files
            soundscape_type: Type of soundscape to find (e.g., "nature", "rain")
            
        Returns:
            Optional[str]: Path to a matching soundscape file or None if not found
        """
        import glob
        
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