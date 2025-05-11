"""
State management utilities for the meditation TTS system.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any

from meditation_tts.config.constants import STATE_DIR, WORKFLOW_STEPS
from meditation_tts.models.state import GraphState

logger = logging.getLogger('meditation_tts')

def save_state(state: GraphState, step: str) -> str:
    """
    Save the current state to a JSON file.
    
    Args:
        state: The current workflow state
        step: The workflow step name
        
    Returns:
        str: Path to the saved state file
    """
    os.makedirs(STATE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"state_{step}_{timestamp}.json"
    filepath = os.path.join(STATE_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
    
    return filepath

def load_state(filepath: str) -> Optional[GraphState]:
    """
    Load state from a JSON file.
    
    Args:
        filepath: Path to the state file
        
    Returns:
        Optional[GraphState]: The loaded state or None if loading failed
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state from {filepath}: {str(e)}")
        return None

def get_latest_state_file(step: Optional[str] = None) -> Optional[str]:
    """
    Get the path to the latest state file, optionally filtered by step.
    
    Args:
        step: Optional workflow step to filter by
        
    Returns:
        Optional[str]: Path to the latest state file or None if not found
    """
    try:
        if not os.path.exists(STATE_DIR):
            logger.warning(f"State directory does not exist: {STATE_DIR}")
            return None
            
        logger.info(f"Looking for latest state file{f' for step {step}' if step else ''}")
        
        # List all state files
        all_files = [f for f in os.listdir(STATE_DIR) if f.startswith("state_")]
        logger.info(f"Found {len(all_files)} total state files")
        
        if not all_files:
            logger.warning("No state files found")
            return None
            
        # Filter by step if requested
        if step:
            # Match the exact step (state_step_timestamp.json format)
            matching_files = [f for f in all_files if f.startswith(f"state_{step}_")]
            if not matching_files:
                logger.warning(f"No state files found for step: {step}")
                return None
                
            logger.info(f"Found {len(matching_files)} state files for step {step}")
            
            # Sort by timestamp in filename (most recent last)
            latest_file = sorted(matching_files)[-1]
            logger.info(f"Latest state file for step {step}: {latest_file}")
            return os.path.join(STATE_DIR, latest_file)
        else:
            # Get all steps in order
            step_prefixes = [f"state_{s}_" for s in WORKFLOW_STEPS]
            
            # Find the latest file for each step
            latest_step_files = []
            for prefix in step_prefixes:
                matching_files = [f for f in all_files if f.startswith(prefix)]
                if matching_files:
                    latest_step_files.append(sorted(matching_files)[-1])
            
            if not latest_step_files:
                logger.warning("No matching state files found")
                return None
                
            # Sort by step order in workflow
            latest_file = sorted(latest_step_files, 
                                key=lambda f: WORKFLOW_STEPS.index(f.split('_')[1]))[-1]
            
            logger.info(f"Latest overall state file: {latest_file}")
            return os.path.join(STATE_DIR, latest_file)
            
    except Exception as e:
        logger.error(f"Error finding latest state file: {str(e)}")
        return None 