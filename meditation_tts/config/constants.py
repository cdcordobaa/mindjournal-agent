"""
Constants for the meditation TTS system.
"""

import os
from pathlib import Path

# File paths and directories
AUDIO_OUTPUT_DIR = "output/audio"
JSON_OUTPUT_DIR = "output/json"
SOUNDSCAPE_DIR = "soundscapes"
STATE_DIR = "output/state"

# Workflow steps
WORKFLOW_STEPS = [
    "generate_script",
    "analyze_prosody",
    "create_profile",
    "generate_ssml",
    "review_and_improve_ssml",
    "generate_audio",
    "mix_audio"
] 