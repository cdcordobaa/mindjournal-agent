"""
Logging utilities for the meditation TTS system.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("meditation_workflow.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('meditation_tts')

def log_state_transition(current_step: str, state: Dict[str, Any]) -> None:
    """Log detailed information about the current state of the workflow."""
    logger.info(f"===== STEP: {current_step} =====")
    
    # Log only the essential state information without huge content
    state_log = {}
    for key, value in state.items():
        if key == "meditation_script" and value:
            state_log[key] = {"length": len(value.get("content", "")), "sections": len(value.get("sections", []))}
        elif key == "prosody_analysis" and value:
            state_log[key] = {"overall_tone": value.get("overall_tone", ""), "key_terms_count": len(value.get("key_terms", []))}
        elif key == "prosody_profile" and value:
            state_log[key] = {"base_rate": value.get("rate", {}).get("base_rate", "") if isinstance(value.get("rate"), dict) else ""}
        elif key == "ssml_output" and value:
            state_log[key] = {"length": len(value), "has_speak_tag": "<speak>" in value and "</speak>" in value}
        elif key == "audio_output" and value:
            state_log[key] = {"status": value.get("status", ""), "voice_file": value.get("voice_file", "")}
        else:
            state_log[key] = value
    
    logger.info(f"State summary: {json.dumps(state_log, indent=2)}")

def log_llm_interaction(prompt: str, response_content: str, model: str, purpose: str) -> None:
    """Log details of an LLM interaction."""
    logger.info(f"LLM Interaction: {purpose}")
    logger.info(f"Model: {model}")
    
    # Log truncated versions of prompt and response
    prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
    response_preview = response_content[:500] + "..." if len(response_content) > 500 else response_content
    
    logger.info(f"Prompt preview: {prompt_preview}")
    logger.info(f"Response preview: {response_preview}")
    
    # Also log the full interaction to a separate file for detailed analysis
    detailed_log_path = f"logs/llm_interactions/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{purpose.replace(' ', '_')}.json"
    os.makedirs(os.path.dirname(detailed_log_path), exist_ok=True)
    
    with open(detailed_log_path, 'w') as f:
        json.dump({
            "purpose": purpose,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response_content
        }, f, indent=2)
    
    logger.info(f"Detailed log saved to: {detailed_log_path}") 