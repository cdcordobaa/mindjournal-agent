# Meditation Audio Generator

This tool generates audio from meditation scripts using AWS Polly text-to-speech service.

## Requirements

- Python 3.6+
- AWS account with Polly access
- boto3 Python package

## Installation

1. Clone this repository

2. Install the required dependencies:

```bash
pip install boto3
```

3. Configure AWS credentials:

   Option 1: Set environment variables:

   ```bash
   export AWS_ACCESS_KEY_ID='your-access-key'
   export AWS_SECRET_ACCESS_KEY='your-secret-key'
   export AWS_DEFAULT_REGION='us-east-1'
   ```

   Option 2: Configure AWS CLI profile:

   ```bash
   aws configure --profile your-profile-name
   ```

   Then set the profile name:

   ```bash
   export AWS_PROFILE='your-profile-name'
   ```

## Usage

### Using the command-line script

```bash
python generate_meditation_audio.py path/to/meditation.json
```

This will process the meditation JSON file and generate an MP3 audio file in the `./audio` directory.

### Using the AudioGenerator class in your code

```python
from audio_generator import AudioGenerator

# Create an instance of AudioGenerator
generator = AudioGenerator(
    aws_profile='your-profile-name',  # Optional: AWS profile name
    # Or provide credentials directly:
    # aws_access_key_id='your-access-key',
    # aws_secret_access_key='your-secret-key',
    aws_region='us-east-1',
    output_dir='./audio'
)

# Test AWS connection
if not generator.test_aws_connection():
    print("AWS connection failed")
    exit(1)

# Generate audio from a meditation JSON file
audio_file = generator.process_meditation_json('path/to/meditation.json')

if audio_file:
    print(f"Audio generated: {audio_file}")
else:
    print("Failed to generate audio")
```

### Using the module's main function

```bash
python audio_generator.py --json_file path/to/meditation.json --profile your-aws-profile --region us-east-1 --output_dir ./audio
```

## Input JSON Format

The module expects a JSON file with the following structure:

```json
{
  "request": {
    "voice_type": "Female", // "Male", "Female", or "Neutral"
    "language_code": "es-ES" // Language code like "en-US", "es-ES", etc.
  },
  "ssml_output": "<speak>...</speak>" // SSML formatted text
}
```

## Supported Voices

The module supports different voices based on the language:

- English (en-US):

  - Male: Matthew
  - Female: Joanna
  - Neutral: Ivy

- Spanish (es-ES):
  - Male: Andrés
  - Female: Conchita
  - Neutral: Mia

## Troubleshooting

If you encounter credential errors, make sure:

1. Your AWS credentials are correctly set up
2. The credentials have access to AWS Polly service
3. You're using the correct region

For other issues, check the error messages for specific details.
