#!/usr/bin/env python
"""
Runner script for Meditation TTS System
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from meditation_tts.main import main

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main function
    main() 