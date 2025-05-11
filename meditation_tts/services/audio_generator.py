"""
AWS Polly-based audio generation service.
"""

import boto3
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any

from meditation_tts.models.enums import VoiceType
from meditation_tts.utils.logging_utils import logger

class AudioGenerator:
    """Service for generating audio from SSML content using AWS Polly."""
    
    # Voice mappings for different languages
    VOICE_MAPS = {
        'es-ES': {
            VoiceType.MALE.value: 'Andrés',
            VoiceType.FEMALE.value: 'Conchita',
            VoiceType.NEUTRAL.value: 'Mia'  # Default to Mia when neutral is requested
        },
        'en-US': {
            VoiceType.MALE.value: 'Matthew',
            VoiceType.FEMALE.value: 'Joanna',
            VoiceType.NEUTRAL.value: 'Ivy'
        }
    }
    
    def __init__(self, aws_profile: Optional[str] = None, 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_region: str = 'us-east-1',
                 output_dir: str = "./"):
        """
        Initialize the AudioGenerator with AWS credentials.
        
        Args:
            aws_profile: AWS profile name to use
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region name
            output_dir: Directory to save generated audio files
        """
        self.output_dir = output_dir
        
        # Create AWS session
        if aws_profile:
            self.session = boto3.Session(profile_name=aws_profile)
        elif aws_access_key_id and aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
        else:
            # Use default credentials
            self.session = boto3.Session(region_name=aws_region)
        
        # Create Polly client
        self.polly_client = self.session.client('polly')
        
    def test_aws_connection(self) -> bool:
        """
        Test AWS connection by listing S3 buckets.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            s3_client = self.session.client('s3')
            s3_client.list_buckets()
            return True
        except ClientError as e:
            logger.error(f"Error accessing AWS: {e}")
            return False
    
    def generate_audio_from_ssml(self, ssml_text: str, voice_id: str, 
                                language_code: str = 'en-US',
                                output_format: str = 'mp3',
                                file_suffix: str = "") -> Optional[str]:
        """
        Generate audio from SSML text using AWS Polly.
        
        Args:
            ssml_text: SSML formatted text
            voice_id: Polly voice ID
            language_code: Language code (e.g., 'en-US', 'es-ES')
            output_format: Output audio format (mp3, ogg_vorbis, pcm)
            file_suffix: Optional suffix for the output filename
            
        Returns:
            Optional[str]: Path to the generated audio file or None if failed
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            response = self.polly_client.synthesize_speech(
                Text=ssml_text,
                TextType='ssml',
                OutputFormat=output_format,
                VoiceId=voice_id,
                LanguageCode=language_code,
            )
            
            if "AudioStream" in response:
                os.makedirs(self.output_dir, exist_ok=True)
                file_name = os.path.join(
                    self.output_dir, 
                    f"meditation_audio_{voice_id}_{timestamp}{file_suffix}.{output_format}"
                )
                with open(file_name, 'wb') as file:
                    file.write(response['AudioStream'].read())
                logger.info(f"Audio content written to file {file_name}")
                return file_name
            else:
                logger.error("Could not generate audio: No AudioStream in response")
                return None
        except ClientError as e:
            logger.error(f"An error occurred with AWS Polly: {e}")
            return None
    
    def generate_chunked_audio(self, ssml_text: str, voice_id: str, 
                             language_code: str = 'en-US',
                             output_format: str = 'mp3',
                             max_chunk_size: int = 2900) -> Optional[str]:
        """
        Generate audio from long SSML text by chunking it into smaller parts.
        
        Args:
            ssml_text: SSML formatted text
            voice_id: Polly voice ID
            language_code: Language code (e.g., 'en-US', 'es-ES')
            output_format: Output audio format (mp3, ogg_vorbis, pcm)
            max_chunk_size: Maximum size of each chunk in characters
            
        Returns:
            Optional[str]: Path to the combined audio file or None if failed
        """
        # Check if SSML is already within limits
        if len(ssml_text) <= max_chunk_size:
            logger.info("SSML text is within limits, no chunking needed")
            return self.generate_audio_from_ssml(ssml_text, voice_id, language_code, output_format)
        
        # Log the chunking operation
        logger.info(f"SSML exceeds AWS Polly length limit ({len(ssml_text)} chars), splitting into chunks")
        
        try:
            # Parse the SSML
            from bs4 import BeautifulSoup
            import re
            
            # Check if we have valid SSML
            if not (ssml_text.strip().startswith("<speak") and ssml_text.strip().endswith("</speak>")):
                logger.warning("Input is not valid SSML, attempting to fix")
                ssml_text = f"<speak>{ssml_text}</speak>"
            
            soup = BeautifulSoup(ssml_text, 'xml')
            speak_tag = soup.find('speak')
            
            if not speak_tag:
                logger.error("Could not parse SSML: speak tag not found")
                return None
            
            # Get all paragraphs
            paragraphs = speak_tag.find_all('p')
            
            if not paragraphs:
                # If no paragraph tags, try to split by sentence tags
                paragraphs = speak_tag.find_all('s')
            
            chunks = []
            
            if paragraphs:
                # Using existing paragraph structure
                logger.info(f"Splitting SSML using {len(paragraphs)} paragraph tags")
                
                current_chunk = "<speak>"
                
                for p in paragraphs:
                    p_str = str(p)
                    if len(current_chunk) + len(p_str) + 10 <= max_chunk_size:  # 10 char buffer for closing tag
                        current_chunk += p_str
                    else:
                        current_chunk += "</speak>"
                        chunks.append(current_chunk)
                        current_chunk = "<speak>" + p_str
                
                # Add the last chunk if not empty
                if current_chunk != "<speak>":
                    current_chunk += "</speak>"
                    chunks.append(current_chunk)
            else:
                # No paragraph structure, use simple text extraction and sentence splitting
                logger.info("No paragraph structure found, splitting by sentences")
                
                # Extract the text content
                text_content = re.sub(r'<[^>]+>', '', str(speak_tag))
                # Split by periods (basic sentence splitting)
                sentences = re.split(r'(?<=[.!?])\s+', text_content)
                
                # Create chunks of sentences
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 50 <= max_chunk_size:  # 50 char buffer for SSML tags
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(f"<speak>{current_chunk.strip()}</speak>")
                        current_chunk = sentence + " "
                
                # Add the last chunk if not empty
                if current_chunk:
                    chunks.append(f"<speak>{current_chunk.strip()}</speak>")
            
            logger.info(f"Split SSML into {len(chunks)} chunks")
            
            # Generate audio for each chunk
            audio_files = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Generating audio for chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                chunk_file = self.generate_audio_from_ssml(
                    ssml_text=chunk,
                    voice_id=voice_id,
                    language_code=language_code,
                    output_format=output_format,
                    file_suffix=f"_chunk_{i+1}"
                )
                
                if chunk_file:
                    audio_files.append(chunk_file)
                    logger.info(f"Generated chunk {i+1}/{len(chunks)}: {chunk_file}")
                else:
                    logger.error(f"Failed to generate audio for chunk {i+1}/{len(chunks)}")
                    return None
            
            # If there's only one file, return it directly
            if len(audio_files) == 1:
                return audio_files[0]
            
            # Combine all audio files using ffmpeg
            import subprocess
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            list_file = os.path.join(self.output_dir, f"chunks_list_{timestamp}.txt")
            combined_file = os.path.join(self.output_dir, f"meditation_voice_{timestamp}.{output_format}")
            
            # Create a list file for ffmpeg
            with open(list_file, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")
            
            # Combine the files using ffmpeg
            try:
                cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", combined_file]
                subprocess.run(cmd, check=True)
                logger.info(f"Combined {len(audio_files)} audio chunks into: {combined_file}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to combine audio chunks: {str(e)}")
                return None
            
            # Clean up intermediate files
            try:
                os.remove(list_file)
                for audio_file in audio_files:
                    os.remove(audio_file)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary files: {str(e)}")
            
            return combined_file
        
        except Exception as e:
            logger.exception(f"Error in chunked audio generation: {str(e)}")
            return None
    
    def process_meditation_json(self, json_file_path: str) -> Optional[str]:
        """
        Process a meditation JSON file to generate audio.
        
        Args:
            json_file_path: Path to the meditation JSON file
            
        Returns:
            Optional[str]: Path to the generated audio file or None if failed
        """
        try:
            # Read the meditation JSON file
            with open(json_file_path, 'r') as f:
                meditation_data = json.load(f)
            
            # Extract required information
            ssml_content = meditation_data.get('ssml_output')
            if not ssml_content:
                logger.error(f"Error: No SSML output found in {json_file_path}")
                return None
                
            # Extract request parameters
            request = meditation_data.get('request', {})
            voice_type_str = request.get('voice_type', 'Female')
            language_code = request.get('language_code', 'en-US')
            
            # Map voice type string to enum
            voice_type_map = {
                'Male': VoiceType.MALE.value,
                'Female': VoiceType.FEMALE.value,
                'Neutral': VoiceType.NEUTRAL.value
            }
            voice_type = voice_type_map.get(voice_type_str, VoiceType.NEUTRAL.value)
            
            # Get the appropriate voice ID
            voice_map = self.VOICE_MAPS.get(language_code, self.VOICE_MAPS['en-US'])
            voice_id = voice_map.get(voice_type, voice_map[VoiceType.NEUTRAL.value])
            
            # Generate audio
            return self.generate_audio_from_ssml(
                ssml_content, 
                voice_id=voice_id,
                language_code=language_code
            )
            
        except Exception as e:
            logger.error(f"Error processing meditation JSON: {e}")
            return None 