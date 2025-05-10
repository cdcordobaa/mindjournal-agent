# Meditation Audio Generator

This tool generates audio from meditation scripts using AWS Polly text-to-speech service and can merge the generated voice with background soundscapes.

## Requirements

- Python 3.6+
- AWS account with Polly access
- boto3 Python package
- pydub Python package (for audio mixing)
- ffmpeg (for audio processing)

## Installation

1. Clone this repository

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install ffmpeg (required for audio processing):

   On macOS:
   ```bash
   brew install ffmpeg
   ```

   On Ubuntu/Debian:
   ```bash
   sudo apt-get install ffmpeg
   ```

   On Windows, download from https://ffmpeg.org/download.html

4. Configure AWS credentials:

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

### Using the command-line script for voice generation

```bash
python generate_meditation_audio.py path/to/meditation.json
```

This will process the meditation JSON file and generate an MP3 audio file in the `./output` directory.

### Using the audio mixer to add background soundscapes

After generating the voice audio, you can merge it with background soundscapes:

```bash
python src/test_audio_mixer.py --voice path/to/voice.mp3 --soundscape_type nature
```

#### Audio Mixer Options:

- `--voice` or `-v`: Path to the voice audio file (required if no MP3 files in output directory)
- `--soundscape_dir` or `-s`: Directory containing soundscape files (default: ./soundscapes)
- `--soundscape_type` or `-t`: Type of soundscape to use (default: nature)
- `--soundscape_file` or `-f`: Direct path to soundscape file (overrides soundscape_type)
- `--output_dir` or `-o`: Directory to save merged audio files (default: ./output)

The script will:
1. Look for soundscape files that match the requested type (or use the directly specified file)
2. Merge the voice with the selected soundscape
3. Create a full-length audio file and a 30-second sample

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

### Add soundscapes to voices programmatically

```python
from src.audio_mixer import process_meditation_audio

# After generating voice audio with Polly
voice_file = "output/meditation_voice.mp3"

# Option 1: Use automatic soundscape selection by type
soundscape_dir = "soundscapes"
soundscape_type = "ocean"  # Can be: nature, rain, ocean, ambient, urban, etc.
output_dir = "output"

full_audio, sample_audio = process_meditation_audio(
    voice_file=voice_file,
    soundscape_dir=soundscape_dir,
    soundscape_type=soundscape_type,
    output_dir=output_dir
)

# Option 2: Use a specific soundscape file
specific_soundscape = "soundscapes/ocean_waves_calm.mp3"

full_audio, sample_audio = process_meditation_audio(
    voice_file=voice_file,
    soundscape_file=specific_soundscape,
    output_dir=output_dir
)

if full_audio:
    print(f"Full meditation audio: {full_audio}")
    print(f"Sample preview: {sample_audio}")
else:
    print("Failed to process meditation audio")
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

## Preparing Soundscape Files

1. Create a directory named `soundscapes` in the project root.
2. Add MP3 files with background sounds to this directory.
3. Name the files descriptively to help with automatic classification:
   - Nature sounds: Include "nature", "forest", "birds", etc. in the filename
   - Rain sounds: Include "rain", "thunder", "storm", etc.
   - Ocean sounds: Include "ocean", "waves", "sea", etc.
   - Ambient sounds: Include "ambient", "background", etc.
   - Urban sounds: Include "urban", "city", "cafe", etc.

Example: `peaceful_forest_nature.mp3`, `ocean_waves_calm.mp3`, `rain_light.mp3`

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

### Audio Mixing Issues

If you encounter issues with audio mixing:

1. Make sure ffmpeg is installed and available in your PATH
2. Verify pydub is installed with `pip install pydub`
3. Check that your soundscape files are valid MP3, WAV, OGG, or FLAC files
4. Look at the logs (printed to console) for specific error messages
