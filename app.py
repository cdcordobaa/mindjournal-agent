"""
Meditation TTS Generator - Streamlit UI

This application provides a user interface for the meditation TTS system.
"""

import os
import streamlit as st
import json
from datetime import datetime
import time
from pathlib import Path
import base64

from meditation_tts.models.enums import (
    EmotionalState,
    MeditationStyle,
    MeditationTheme,
    VoiceType,
    SoundscapeType
)
from meditation_tts.workflow.runner import run_meditation_generation
from meditation_tts.utils.logging_utils import logger
from meditation_tts.config.constants import WORKFLOW_STEPS

# Set page configuration
st.set_page_config(
    page_title="Meditation TTS Generator",
    page_icon="🧘‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a calming interface
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f3f5;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e2eafc;
    }
    .stButton>button {
        background-color: #a2d2ff;
        color: #333;
        font-weight: 600;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #bde0fe;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .progress-message {
        background-color: #e2eafc;
        color: #1e3a8a;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #3b82f6;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .info-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 20px;
        border: 1px solid #dee2e6;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def get_audio_download_link(file_path, link_text):
    """Generate a download link for an audio file"""
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    return f'<a href="data:audio/mp3;base64,{b64_audio}" download="{os.path.basename(file_path)}">{link_text}</a>'

def display_step_status(completed_steps, current_step):
    """Display the status of workflow steps"""
    total_steps = len(WORKFLOW_STEPS)
    step_descriptions = {
        "generate_script": "Generating meditation script",
        "analyze_prosody": "Analyzing prosody needs",
        "create_profile": "Creating prosody profile",
        "generate_ssml": "Generating SSML markup",
        "review_and_improve_ssml": "Reviewing and improving SSML",
        "generate_audio": "Generating audio",
        "mix_audio": "Mixing with soundscape"
    }
    
    progress_value = len(completed_steps) / total_steps
    progress_bar = st.progress(progress_value)
    
    for i, step in enumerate(WORKFLOW_STEPS):
        if step in completed_steps:
            st.markdown(f"✅ **{step_descriptions.get(step, step)}** - Completed")
        elif step == current_step:
            st.markdown(f"⏳ **{step_descriptions.get(step, step)}** - In progress")
        else:
            st.markdown(f"⏱️ **{step_descriptions.get(step, step)}** - Pending")
    
    return progress_bar

def init_session_state():
    """Initialize session state variables"""
    if 'generated_meditation' not in st.session_state:
        st.session_state.generated_meditation = None
    if 'generation_completed' not in st.session_state:
        st.session_state.generation_completed = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = None
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = []
    if 'error' not in st.session_state:
        st.session_state.error = None
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'config_history' not in st.session_state:
        st.session_state.config_history = []

def save_config_to_history(config):
    """Save current configuration to history"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = f"{config['meditation_theme']} ({timestamp})"
    st.session_state.config_history.append({
        "name": name,
        "config": config.copy(),
        "timestamp": timestamp
    })

def create_meditation(request_data):
    """Run the meditation generation workflow and update session state"""
    try:
        st.session_state.loading = True
        st.session_state.start_time = time.time()
        st.session_state.error = None
        st.session_state.completed_steps = []
        st.session_state.current_step = WORKFLOW_STEPS[0]
        
        # Prepare for step by step tracking
        progress_placeholder = st.empty()
        
        # Run the workflow with custom tracking
        for step in WORKFLOW_STEPS:
            st.session_state.current_step = step
            
            # Display updated progress
            with progress_placeholder.container():
                progress_bar = display_step_status(st.session_state.completed_steps, st.session_state.current_step)
            
            # Run just this step
            result = run_meditation_generation(
                request_data, 
                start_step=step, 
                end_step=step,
                initial_state=st.session_state.generated_meditation if st.session_state.generated_meditation else None
            )
            
            # Update session state with result
            st.session_state.generated_meditation = result
            
            # Check for errors
            if result.get("error"):
                st.session_state.error = result.get("error")
                break
                
            # Mark step as completed
            st.session_state.completed_steps.append(step)
            
            # Update progress
            with progress_placeholder.container():
                progress_bar = display_step_status(st.session_state.completed_steps, 
                                                   WORKFLOW_STEPS[WORKFLOW_STEPS.index(step) + 1] if WORKFLOW_STEPS.index(step) < len(WORKFLOW_STEPS) - 1 else None)
        
        st.session_state.generation_completed = len(st.session_state.completed_steps) == len(WORKFLOW_STEPS)
        if st.session_state.generation_completed:
            save_config_to_history(request_data)
            
    except Exception as e:
        st.session_state.error = str(e)
        logger.error(f"Error generating meditation: {e}")
    finally:
        st.session_state.loading = False

def main():
    """Main function for the Streamlit app"""
    init_session_state()
    
    # App header
    st.title("🧘‍♀️ Meditation Generator")
    st.markdown("Generate personalized guided meditations with natural speech and background soundscapes.")
    
    # Create tabs for different sections
    tabs = st.tabs(["Create Meditation", "Preview & Download", "My Meditations", "Advanced Settings", "History"])
    
    with tabs[0]:  # Create Meditation tab
        st.subheader("Meditation Configuration")
        
        # Create two columns for form layout
        col1, col2 = st.columns(2)
        
        with col1:
            emotional_state = st.selectbox(
                "How are you feeling?", 
                options=[e.value for e in EmotionalState], 
                index=2,  # Default to ANXIOUS
                help="Select your current emotional state to personalize the meditation"
            )
            
            meditation_style = st.selectbox(
                "Meditation Style", 
                options=[s.value for s in MeditationStyle], 
                index=0,  # Default to MINDFULNESS
                help="The type of meditation technique to be used"
            )
            
            meditation_theme = st.selectbox(
                "Meditation Theme", 
                options=[t.value for t in MeditationTheme], 
                index=0,  # Default to STRESS_RELIEF
                help="The primary focus or goal of this meditation session"
            )
        
        with col2:
            duration = st.slider(
                "Duration (minutes)", 
                min_value=3, 
                max_value=30, 
                value=10, 
                step=1,
                help="Length of the meditation in minutes"
            )
            
            voice_type = st.selectbox(
                "Voice Type", 
                options=[v.value for v in VoiceType], 
                index=1,  # Default to FEMALE
                help="Select the type of voice you prefer for guidance"
            )
            
            language_code = st.selectbox(
                "Language", 
                options=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT"], 
                index=0,
                help="Language for the meditation narration"
            )
            
            soundscape = st.selectbox(
                "Background Soundscape", 
                options=[s.value for s in SoundscapeType], 
                index=0,  # Default to NATURE
                help="Select background ambient sounds to accompany your meditation"
            )
        
        # Preview soundscape (placeholder - would need actual samples)
        with st.expander("Preview Soundscape Sample"):
            st.info("Soundscape preview would play here (30 second sample)")
            # Here you would include audio player with sample files if available
        
        # Create meditation button
        generate_button = st.button("Generate My Meditation", type="primary", use_container_width=True)
        
        if generate_button:
            # Check for API key
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                st.error("OpenAI API key not found. Please set your OPENAI_API_KEY environment variable.")
            else:
                # Collect request data
                request_data = {
                    "emotional_state": emotional_state,
                    "meditation_style": meditation_style,
                    "meditation_theme": meditation_theme,
                    "duration_minutes": duration,
                    "voice_type": voice_type,
                    "language_code": language_code,
                    "soundscape": soundscape
                }
                
                # Run generation in session state
                create_meditation(request_data)
        
        # Show loading or error states
        if st.session_state.loading:
            elapsed_time = time.time() - st.session_state.start_time
            st.markdown(f"""
            <div class="progress-message">
                Generating your meditation... (Elapsed time: {int(elapsed_time)} seconds)<br>
                This may take several minutes depending on the duration and complexity.
            </div>
            """, unsafe_allow_html=True)
            
        if st.session_state.error:
            st.error(f"Error generating meditation: {st.session_state.error}")
    
    with tabs[1]:  # Preview & Download tab
        if st.session_state.generation_completed and st.session_state.generated_meditation:
            result = st.session_state.generated_meditation
            
            st.markdown("""
            <div class="success-message">
                Your meditation has been generated successfully! You can preview it below or download the files.
            </div>
            """, unsafe_allow_html=True)
            
            # Display generated meditation info
            st.subheader("Your Meditation")
            
            # Create two columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Basic info card
                st.markdown("""
                <div class="info-box">
                    <h4>Meditation Details</h4>
                """, unsafe_allow_html=True)
                
                if "request" in result:
                    st.write(f"**Theme:** {result['request'].get('meditation_theme', 'Unknown')}")
                    st.write(f"**Style:** {result['request'].get('meditation_style', 'Unknown')}")
                    st.write(f"**Duration:** {result['request'].get('duration_minutes', 'Unknown')} minutes")
                    st.write(f"**Voice:** {result['request'].get('voice_type', 'Unknown')}")
                    st.write(f"**Soundscape:** {result['request'].get('soundscape', 'Unknown')}")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                # Audio player card
                st.markdown("""
                <div class="info-box">
                    <h4>Listen to Your Meditation</h4>
                """, unsafe_allow_html=True)
                
                if result.get("audio_output") and result["audio_output"].get("final_output_path"):
                    final_path = result["audio_output"]["final_output_path"]
                    
                    if os.path.exists(final_path):
                        st.audio(final_path)
                        
                        # Download link
                        st.markdown(get_audio_download_link(final_path, "Download Meditation Audio"), unsafe_allow_html=True)
                    else:
                        st.warning(f"Audio file not found at: {final_path}")
                else:
                    st.info("Audio file information not available")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Meditation script
            with st.expander("View Meditation Script", expanded=False):
                if result.get("meditation_script") and result["meditation_script"].get("content"):
                    st.markdown("### Meditation Script")
                    st.markdown(result["meditation_script"]["content"])
                else:
                    st.info("Meditation script not available")
        
        else:
            st.info("No meditation has been generated yet. Go to the 'Create Meditation' tab to generate one.")
    
    with tabs[2]:  # My Meditations tab
        st.subheader("My Meditation Library")
        st.markdown("Browse and play your previously generated meditations.")
        
        # Find all available meditations
        audio_dir = "output/audio"
        json_dir = "output/json"
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        
        # Find audio files and their metadata
        found_meditations = []
        
        # Look for audio files
        if os.path.exists(audio_dir):
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav'))]
            
            for audio_file in audio_files:
                file_path = os.path.join(audio_dir, audio_file)
                
                # Extract info from filename
                meditation_info = {}
                meditation_info['filename'] = audio_file
                meditation_info['path'] = file_path
                meditation_info['size'] = f"{os.path.getsize(file_path) / (1024*1024):.1f} MB"
                
                # Try to get creation time
                try:
                    timestamp = os.path.getctime(file_path)
                    meditation_info['created'] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    meditation_info['created'] = "Unknown"
                
                # Try to extract theme and style from filename
                name_parts = audio_file.replace('.mp3', '').replace('.wav', '').split('_')
                if len(name_parts) >= 2:
                    meditation_info['theme'] = name_parts[0]
                    meditation_info['style'] = name_parts[1] if len(name_parts) > 1 else "Unknown"
                else:
                    meditation_info['theme'] = "Unknown"
                    meditation_info['style'] = "Unknown"
                
                # Look for matching JSON metadata
                json_filename = audio_file.replace('.mp3', '.json').replace('.wav', '.json')
                json_path = os.path.join(json_dir, json_filename)
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            metadata = json.load(f)
                            if "request" in metadata:
                                req = metadata["request"]
                                meditation_info['theme'] = req.get("meditation_theme", meditation_info['theme'])
                                meditation_info['style'] = req.get("meditation_style", meditation_info['style'])
                                meditation_info['duration'] = req.get("duration_minutes", "Unknown")
                                meditation_info['emotional_state'] = req.get("emotional_state", "Unknown")
                                meditation_info['voice_type'] = req.get("voice_type", "Unknown")
                                meditation_info['soundscape'] = req.get("soundscape", "Unknown")
                                meditation_info['metadata_path'] = json_path
                    except:
                        pass
                
                found_meditations.append(meditation_info)
        
        # Sort by creation date (newest first)
        found_meditations.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        if found_meditations:
            # Display as a grid of cards
            st.markdown("### Your Meditations")
            
            # Define filter options
            filter_options = ["All"]
            themes = set(m.get('theme', "Unknown") for m in found_meditations if m.get('theme') != "Unknown")
            styles = set(m.get('style', "Unknown") for m in found_meditations if m.get('style') != "Unknown")
            
            filter_options.extend(sorted(themes))
            
            # Add filter
            selected_filter = st.selectbox("Filter by theme", options=filter_options)
            
            # Filter meditations based on selection
            if selected_filter != "All":
                filtered_meditations = [m for m in found_meditations if m.get('theme') == selected_filter]
            else:
                filtered_meditations = found_meditations
            
            if not filtered_meditations:
                st.info(f"No meditations found with theme: {selected_filter}")
            
            # Create responsive grid (3 columns)
            cols = st.columns(3)
            
            for i, meditation in enumerate(filtered_meditations):
                col_idx = i % 3
                
                with cols[col_idx]:
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                            <h4>{meditation.get('theme', 'Meditation')} - {meditation.get('style', '')}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display info
                        st.markdown(f"**Created:** {meditation.get('created', 'Unknown')}")
                        if 'duration' in meditation:
                            st.markdown(f"**Duration:** {meditation.get('duration')} minutes")
                        if 'emotional_state' in meditation:
                            st.markdown(f"**For:** {meditation.get('emotional_state')} state")
                        if 'voice_type' in meditation:
                            st.markdown(f"**Voice:** {meditation.get('voice_type')}")
                        if 'soundscape' in meditation:
                            st.markdown(f"**Soundscape:** {meditation.get('soundscape')}")
                        
                        # Audio player
                        st.audio(meditation['path'])
                        
                        # Download link
                        st.markdown(get_audio_download_link(meditation['path'], "Download"), unsafe_allow_html=True)
                        
                        # Expand for more options
                        with st.expander("More Options"):
                            # View metadata if available
                            if 'metadata_path' in meditation:
                                if st.button(f"View Details", key=f"view_details_{i}"):
                                    try:
                                        with open(meditation['metadata_path'], 'r') as f:
                                            metadata = json.load(f)
                                        
                                        st.json(metadata)
                                        
                                        # If there's a script, display it
                                        if "meditation_script" in metadata and metadata["meditation_script"] and "content" in metadata["meditation_script"]:
                                            st.markdown("### Meditation Script")
                                            st.markdown(metadata["meditation_script"]["content"])
                                    except Exception as e:
                                        st.error(f"Error loading metadata: {str(e)}")
                            
                            # Load as current meditation button
                            if st.button(f"Load as Current Meditation", key=f"load_current_{i}"):
                                try:
                                    if 'metadata_path' in meditation:
                                        with open(meditation['metadata_path'], 'r') as f:
                                            metadata = json.load(f)
                                        
                                        st.session_state.generated_meditation = metadata
                                        st.session_state.generation_completed = True
                                        st.success(f"Loaded '{meditation.get('theme')}' as current meditation")
                                        st.info("Switch to the 'Preview & Download' tab to see details")
                                except Exception as e:
                                    st.error(f"Error loading meditation: {str(e)}")
        else:
            st.info("No meditation audio files found in your library yet.")
            st.markdown("Generate a meditation using the 'Create Meditation' tab to see it here.")
        
        # Explanation about where files are stored
        with st.expander("About Your Meditation Files"):
            st.markdown(f"""
            ### Where Your Meditations Are Stored
            
            - **Audio files** are stored in: `{os.path.abspath(audio_dir)}`
            - **Metadata files** are stored in: `{os.path.abspath(json_dir)}`
            - **Processing states** are stored in: `{os.path.abspath('output/state')}`
            
            You can access these directories directly to backup or manage your meditation files.
            """)
    
    with tabs[3]:  # Advanced Settings tab
        st.subheader("Advanced Options")
        
        # Technical details expander
        with st.expander("View Technical Details", expanded=False):
            if st.session_state.generated_meditation:
                result = st.session_state.generated_meditation
                
                # SSML Output
                st.markdown("### SSML Markup")
                if result.get("ssml_output"):
                    if isinstance(result["ssml_output"], dict) and result["ssml_output"].get("ssml_content"):
                        st.code(result["ssml_output"]["ssml_content"], language="xml")
                    elif isinstance(result["ssml_output"], str):
                        st.code(result["ssml_output"], language="xml")
                    else:
                        st.info("SSML markup not available in the expected format")
                else:
                    st.info("SSML markup not available")
                
                # Prosody Profile
                st.markdown("### Prosody Profile")
                if result.get("prosody_profile"):
                    st.json(result["prosody_profile"])
                else:
                    st.info("Prosody profile not available")
            else:
                st.info("No meditation has been generated yet.")
        
        # Developer Options
        with st.expander("Developer Options", expanded=False):
            st.markdown("### Workflow Control")
            
            start_step = st.selectbox(
                "Start from step", 
                options=WORKFLOW_STEPS,
                index=0
            )
            
            end_step = st.selectbox(
                "End at step", 
                options=WORKFLOW_STEPS,
                index=len(WORKFLOW_STEPS) - 1
            )
            
            st.warning("Warning: Starting or ending at specific workflow steps is intended for developers. This may result in incomplete meditations if used improperly.")
            
            # Execute custom workflow button
            custom_workflow_button = st.button("Run Custom Workflow", type="secondary", use_container_width=True)
            
            if custom_workflow_button:
                # Check for API key
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    st.error("OpenAI API key not found. Please set your OPENAI_API_KEY environment variable.")
                else:
                    # Get current configuration values
                    # We need to get the values from the session state or form again
                    # In a real application, you would save these values in session state
                    # This is simplified for illustration
                    request_data = {
                        "emotional_state": emotional_state,
                        "meditation_style": meditation_style,
                        "meditation_theme": meditation_theme,
                        "duration_minutes": duration,
                        "voice_type": voice_type,
                        "language_code": language_code,
                        "soundscape": soundscape
                    }
                    
                    # Run custom workflow
                    result = run_meditation_generation(request_data, start_step=start_step, end_step=end_step)
                    st.session_state.generated_meditation = result
                    st.session_state.generation_completed = True if not result.get("error") else False
                    
                    if result.get("error"):
                        st.error(f"Error in workflow: {result['error']}")
                    else:
                        st.success(f"Custom workflow completed successfully from {start_step} to {end_step}")
        
        # Previous Step Resources
        with st.expander("Previous Step Resources", expanded=False):
            st.markdown("### Load Resources from Previous Runs")
            st.markdown("Access state files from previously executed workflow steps to analyze or restart from a specific point.")
            
            # Get state directories
            state_dir = "output/state"
            if os.path.exists(state_dir):
                # Find all step directories
                step_dirs = [d for d in os.listdir(state_dir) if os.path.isdir(os.path.join(state_dir, d))]
                
                if step_dirs:
                    # Select step
                    selected_step = st.selectbox(
                        "Select workflow step",
                        options=step_dirs
                    )
                    
                    # Get state files for the selected step
                    step_path = os.path.join(state_dir, selected_step)
                    state_files = [f for f in os.listdir(step_path) if f.endswith('.json')]
                    
                    if state_files:
                        # Sort files by timestamp (newest first)
                        state_files.sort(reverse=True)
                        
                        # Format file options with timestamps
                        file_options = []
                        for file in state_files:
                            # Extract timestamp from filename
                            timestamp_str = file.split('_')[-1].replace('.json', '')
                            try:
                                # Try to convert timestamp to readable format
                                timestamp = datetime.fromtimestamp(int(timestamp_str))
                                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                                file_options.append(f"{file} ({formatted_time})")
                            except:
                                file_options.append(file)
                        
                        # Select state file
                        selected_file_option = st.selectbox(
                            "Select state file",
                            options=file_options
                        )
                        
                        # Extract actual filename from option
                        selected_file = selected_file_option.split(' (')[0]
                        
                        # Load state
                        load_button = st.button("Load Selected State", key="load_state_button")
                        
                        if load_button:
                            try:
                                from meditation_tts.utils.state_utils import load_state
                                
                                file_path = os.path.join(step_path, selected_file)
                                loaded_state = load_state(file_path)
                                
                                if loaded_state:
                                    st.session_state.generated_meditation = loaded_state
                                    st.success(f"Successfully loaded state from {selected_file}")
                                    
                                    # Display what was loaded
                                    st.markdown("### Loaded State Contents")
                                    
                                    # Show a summary of what's in the state
                                    state_summary = {k: "Present" if v is not None else "None" for k, v in loaded_state.items()}
                                    st.json(state_summary)
                                    
                                    # Option to restart from this state
                                    if st.button("Continue Meditation from this Point"):
                                        # Get the next step after the selected one
                                        if selected_step in WORKFLOW_STEPS:
                                            current_step_idx = WORKFLOW_STEPS.index(selected_step)
                                            if current_step_idx < len(WORKFLOW_STEPS) - 1:
                                                next_step = WORKFLOW_STEPS[current_step_idx + 1]
                                                
                                                # Run from next step
                                                st.info(f"Continuing workflow from step: {next_step}")
                                                
                                                # Get request data from loaded state
                                                request_data = loaded_state.get("request", {})
                                                
                                                # Run remaining workflow
                                                result = run_meditation_generation(
                                                    request_data, 
                                                    start_step=next_step,
                                                    initial_state=loaded_state
                                                )
                                                
                                                st.session_state.generated_meditation = result
                                                st.session_state.generation_completed = True if not result.get("error") else False
                                                
                                                if result.get("error"):
                                                    st.error(f"Error in workflow: {result['error']}")
                                                else:
                                                    st.success(f"Workflow completed successfully from {next_step}")
                                            else:
                                                st.warning("This was the last step. No further steps to continue.")
                                else:
                                    st.error(f"Failed to load state from {selected_file}")
                            except Exception as e:
                                st.error(f"Error loading state: {str(e)}")
                        
                        # View full state contents
                        view_button = st.button("View Full State Contents", key="view_state_button")
                        
                        if view_button:
                            try:
                                file_path = os.path.join(step_path, selected_file)
                                with open(file_path, 'r') as f:
                                    state_content = json.load(f)
                                
                                # Create tabs for different parts of the state
                                state_tabs = st.tabs(["Overview", "Request", "Script", "Prosody", "SSML", "Audio"])
                                
                                with state_tabs[0]:
                                    st.json({k: "Present" if v is not None else "None" for k, v in state_content.items()})
                                
                                with state_tabs[1]:
                                    if "request" in state_content:
                                        st.json(state_content["request"])
                                    else:
                                        st.info("No request data available")
                                
                                with state_tabs[2]:
                                    if "meditation_script" in state_content and state_content["meditation_script"]:
                                        if isinstance(state_content["meditation_script"], dict) and "content" in state_content["meditation_script"]:
                                            st.markdown(state_content["meditation_script"]["content"])
                                        else:
                                            st.json(state_content["meditation_script"])
                                    else:
                                        st.info("No script data available")
                                
                                with state_tabs[3]:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if "prosody_analysis" in state_content and state_content["prosody_analysis"]:
                                            st.subheader("Prosody Analysis")
                                            st.json(state_content["prosody_analysis"])
                                        else:
                                            st.info("No prosody analysis available")
                                    
                                    with col2:
                                        if "prosody_profile" in state_content and state_content["prosody_profile"]:
                                            st.subheader("Prosody Profile")
                                            st.json(state_content["prosody_profile"])
                                        else:
                                            st.info("No prosody profile available")
                                
                                with state_tabs[4]:
                                    if "ssml_output" in state_content and state_content["ssml_output"]:
                                        if isinstance(state_content["ssml_output"], dict) and "ssml_content" in state_content["ssml_output"]:
                                            st.code(state_content["ssml_output"]["ssml_content"], language="xml")
                                        elif isinstance(state_content["ssml_output"], str):
                                            st.code(state_content["ssml_output"], language="xml")
                                        else:
                                            st.json(state_content["ssml_output"])
                                    else:
                                        st.info("No SSML data available")
                                    
                                    if "ssml_review" in state_content and state_content["ssml_review"]:
                                        st.subheader("SSML Review")
                                        st.json(state_content["ssml_review"])
                                
                                with state_tabs[5]:
                                    if "audio_output" in state_content and state_content["audio_output"]:
                                        st.json(state_content["audio_output"])
                                        
                                        # If there's an audio file path, try to play it
                                        audio_path = None
                                        if isinstance(state_content["audio_output"], dict):
                                            if "final_output_path" in state_content["audio_output"]:
                                                audio_path = state_content["audio_output"]["final_output_path"]
                                            elif "output_path" in state_content["audio_output"]:
                                                audio_path = state_content["audio_output"]["output_path"]
                                        
                                        if audio_path and os.path.exists(audio_path):
                                            st.audio(audio_path)
                                    else:
                                        st.info("No audio data available")
                                
                            except Exception as e:
                                st.error(f"Error viewing state: {str(e)}")
                    else:
                        st.info(f"No state files found for step: {selected_step}")
                else:
                    st.info("No workflow step directories found.")
            else:
                st.warning(f"State directory not found: {state_dir}")
                st.markdown("Generate a meditation first to create state files.")
                
            # Explanation
            st.markdown("""
            #### How to use previous step resources
            
            1. Select a workflow step (e.g., `generate_script`, `create_profile`)
            2. Choose a state file (newest files are at the top)
            3. Load the state to examine its contents
            4. Optionally continue the meditation generation from this point
            
            This is useful for debugging or restoring a meditation generation that was interrupted.
            """)
    
    with tabs[4]:  # History tab
        st.subheader("Meditation History")
        
        if not st.session_state.config_history:
            st.info("No meditation history yet. Generate meditations to see them here.")
        else:
            # Display saved configurations
            for i, saved_config in enumerate(st.session_state.config_history):
                with st.expander(f"{saved_config['name']}"):
                    st.write(f"**Created:** {saved_config['timestamp']}")
                    st.write(f"**Theme:** {saved_config['config'].get('meditation_theme')}")
                    st.write(f"**Style:** {saved_config['config'].get('meditation_style')}")
                    st.write(f"**Duration:** {saved_config['config'].get('duration_minutes')} minutes")
                    
                    # Add button to load this configuration
                    if st.button(f"Load Configuration", key=f"load_config_{i}"):
                        # In a real app, this would set the form values
                        st.info(f"Configuration '{saved_config['name']}' loaded")
                        # Here you would update the session state for form values

if __name__ == "__main__":
    main() 