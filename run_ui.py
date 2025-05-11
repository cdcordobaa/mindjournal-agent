#!/usr/bin/env python
"""
Launcher script for the Meditation TTS Generator UI.
"""

import os
import sys
import subprocess
from pathlib import Path
import webbrowser
import time

def check_environment():
    """Check if environment is properly set up"""
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        # Try to load from .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            print("Loading environment variables from .env file...")
            with open(env_path, 'r') as file:
                for line in file:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Check again after attempting to load
        if not os.environ.get("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please create a .env file with your OpenAI API key or set it manually.")
            print("Example: export OPENAI_API_KEY='your-api-key'")
            return False
    
    # Check if required directories exist
    for directory in ["output", "output/audio", "output/json", "output/state"]:
        os.makedirs(directory, exist_ok=True)
    
    return True

def launch_streamlit():
    """Launch the Streamlit UI application"""
    try:
        print("Starting Meditation TTS Generator UI...")
        
        # Start Streamlit in a new process
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "app.py", "--browser.serverAddress", "localhost", 
            "--server.headless", "true"
        ])
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Open in web browser automatically
        webbrowser.open("http://localhost:8501")
        
        print("Meditation TTS Generator UI is running at http://localhost:8501")
        print("Press Ctrl+C to stop the application")
        
        # Keep the script running until interrupted
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping Meditation TTS Generator UI...")
            process.terminate()
            process.wait()
            print("Application stopped.")
    
    except Exception as e:
        print(f"Error launching the application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if check_environment():
        launch_streamlit()
    else:
        sys.exit(1) 