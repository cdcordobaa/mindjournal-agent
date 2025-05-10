import boto3
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError
from enum import Enum
from typing import Optional, Dict, Any


class VoiceType(Enum):
    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"


class AudioGenerator:
    """Module for generating audio from SSML content using AWS Polly"""
    
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
            print(f"Error accessing AWS: {e}")
            return False
    
    def generate_audio_from_ssml(self, ssml_text: str, voice_id: str, 
                                language_code: str = 'en-US',
                                output_format: str = 'mp3') -> Optional[str]:
        """
        Generate audio from SSML text using AWS Polly.
        
        Args:
            ssml_text: SSML formatted text
            voice_id: Polly voice ID
            language_code: Language code (e.g., 'en-US', 'es-ES')
            output_format: Output audio format (mp3, ogg_vorbis, pcm)
            
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
                    f"meditation_audio_{voice_id}_{timestamp}.{output_format}"
                )
                with open(file_name, 'wb') as file:
                    file.write(response['AudioStream'].read())
                print(f"Audio content written to file {file_name}")
                return file_name
            else:
                print("Could not generate audio: No AudioStream in response")
                return None
        except ClientError as e:
            print(f"An error occurred with AWS Polly: {e}")
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
                print(f"Error: No SSML output found in {json_file_path}")
                return None
                
            # Extract request parameters
            request = meditation_data.get('request', {})
            voice_type_str = request.get('voice_type', 'Female')
            language_code = request.get('language_code', 'en-US')
            
            # Map voice type string to enum
            voice_type_map = {
                'Male': VoiceType.MALE,
                'Female': VoiceType.FEMALE,
                'Neutral': VoiceType.NEUTRAL
            }
            voice_type = voice_type_map.get(voice_type_str, VoiceType.NEUTRAL)
            
            # Get the appropriate voice ID
            voice_map = self.VOICE_MAPS.get(language_code, self.VOICE_MAPS['en-US'])
            voice_id = voice_map.get(voice_type.value, voice_map[VoiceType.NEUTRAL.value])
            
            # Generate audio
            return self.generate_audio_from_ssml(
                ssml_content, 
                voice_id=voice_id,
                language_code=language_code
            )
            
        except Exception as e:
            print(f"Error processing meditation JSON: {e}")
            return None


def main():
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate audio from meditation JSON files')
    parser.add_argument('--json_file', required=True, help='Path to the meditation JSON file')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output_dir', default='./audio', help='Output directory for audio files')
    
    args = parser.parse_args()
    
    # Create audio generator
    generator = AudioGenerator(
        aws_profile=args.profile,
        aws_region=args.region,
        output_dir=args.output_dir
    )
    
    # Test AWS connection
    if not generator.test_aws_connection():
        print("AWS connection failed. Please check your credentials.")
        return
    
    # Process meditation JSON
    audio_file = generator.process_meditation_json(args.json_file)
    
    if audio_file:
        print(f"Audio generated successfully: {audio_file}")
    else:
        print("Failed to generate audio")


if __name__ == "__main__":
    main() 