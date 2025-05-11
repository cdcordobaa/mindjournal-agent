# Meditation Generator UI

A Streamlit-based user interface for the Meditation TTS system that allows you to generate personalized, AI-powered guided meditations with natural voice and background soundscapes.

## Features

- **Intuitive Interface**: Clean, distraction-free design appropriate for a meditation application
- **Personalized Meditations**: Select your emotional state, preferred meditation style, theme, and duration
- **Voice Customization**: Choose between different voice types and languages
- **Background Soundscapes**: Add ambient sounds to enhance your meditation experience
- **Live Progress Tracking**: Follow the meditation generation process step by step
- **Meditation History**: Save and reload your favorite meditation configurations
- **Advanced Options**: Access technical details and developer settings (SSML, prosody profiles)

## Getting Started

### Prerequisites

- Python 3.10 or newer
- OpenAI API key

### Installation

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Set your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY="your-api-key"
   ```
   Alternatively, create a `.env` file with your API key.

### Running the Application

Launch the Streamlit app with:

```
streamlit run app.py
```

The application should open in your default web browser at `http://localhost:8501`.

## Usage Guide

### 1. Creating a Meditation

1. Navigate to the "Create Meditation" tab
2. Select your current emotional state
3. Choose a meditation style and theme
4. Set your preferred duration (3-30 minutes)
5. Select voice type and language
6. Choose a background soundscape
7. Click "Generate My Meditation"

The generation process may take several minutes depending on the duration and complexity of your meditation.

### 2. Previewing and Downloading

Once generation is complete:

1. Go to the "Preview & Download" tab
2. Listen to your meditation using the embedded audio player
3. View meditation details and script
4. Download the audio file to your device

### 3. Advanced Features

- **Technical Details**: View the SSML markup and prosody profile used to generate the meditation
- **Developer Options**: Control specific workflow steps for custom meditation generation
- **History**: Access and reload previously generated meditation configurations

## Workflow Steps

The meditation generation follows these steps:

1. **Generate Script**: Creates the meditation script based on your selections
2. **Analyze Prosody**: Analyzes speech patterns needed for natural delivery
3. **Create Profile**: Develops a detailed prosody profile
4. **Generate SSML**: Creates speech markup with appropriate pauses, emphasis, and tone
5. **Review SSML**: Refines the speech markup for optimal delivery
6. **Generate Audio**: Converts the SSML to high-quality audio
7. **Mix Audio**: Combines the voice with your selected background soundscape

## Troubleshooting

- **API Key Error**: Ensure your OpenAI API key is correctly set in your environment variables
- **Audio Not Found**: Check that the output directories exist and have write permissions
- **Generation Errors**: The application will display specific error messages in case of issues

## License

[License information here]

## Acknowledgments

- This UI is powered by Streamlit
- Voice generation uses AWS Polly
- Meditation content generated with LangChain and OpenAI 