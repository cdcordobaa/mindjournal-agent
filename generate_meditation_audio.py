#!/usr/bin/env python3
from audio_generator import AudioGenerator
import os
import sys

def main():
    """
    Generate audio from a meditation JSON file using AWS Polly.
    
    Usage:
        python generate_meditation_audio.py <json_file_path>
    """
    if len(sys.argv) < 2:
        print("Usage: python generate_meditation_audio.py <json_file_path>")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} does not exist")
        sys.exit(1)
    
    # Create output directory
    output_dir = "./audio"
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure AWS credentials - using environment variables or default profile
    # You can set these environment variables before running the script
    # or modify this script to use your credentials directly
    aws_profile = os.environ.get('AWS_PROFILE')
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create audio generator
    generator = AudioGenerator(
        aws_profile=aws_profile,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        output_dir=output_dir
    )
    
    # Test AWS connection
    print("Testing AWS connection...")
    if not generator.test_aws_connection():
        print("AWS connection failed. Please check your credentials.")
        sys.exit(1)
    
    print("AWS connection successful.")
    
    # Process meditation JSON
    print(f"Processing meditation file: {json_file_path}")
    audio_file = generator.process_meditation_json(json_file_path)
    
    if audio_file:
        print(f"Audio generated successfully: {audio_file}")
    else:
        print("Failed to generate audio")
        sys.exit(1)


if __name__ == "__main__":
    main() 