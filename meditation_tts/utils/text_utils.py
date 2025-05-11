"""
Text processing utilities for the meditation TTS system.
"""

import re
from typing import List, Dict, Optional, Any

def split_into_sentences(text: str) -> List[str]:
    """
    Simple sentence splitter for text processing.
    
    Args:
        text: The text to split into sentences
        
    Returns:
        List[str]: A list of sentences
    """
    # Split on periods, question marks, and exclamation points
    # but keep the punctuation with the sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty sentences
    return [s for s in sentences if s.strip()]

def detect_breathing_pattern(sentence: str) -> Optional[Dict[str, Any]]:
    """
    Detect breathing pattern instructions in a sentence.
    
    Args:
        sentence: The sentence to analyze for breathing instructions
        
    Returns:
        Optional[Dict[str, Any]]: Information about the detected breathing pattern or None
    """
    sentence_lower = sentence.lower()
    
    # 4-7-8 breathing pattern
    if any(phrase in sentence_lower for phrase in ["inhala por 4", "inhale for 4", "breathe in for 4"]):
        return {
            "type": "4-7-8",
            "phase": "inhale"
        }
    elif any(phrase in sentence_lower for phrase in ["mantén por 7", "hold for 7", "hold your breath for 7"]):
        return {
            "type": "4-7-8",
            "phase": "hold"
        }
    elif any(phrase in sentence_lower for phrase in ["exhala por 8", "exhale for 8", "breathe out for 8"]):
        return {
            "type": "4-7-8",
            "phase": "exhale"
        }
    
    # Box breathing pattern
    elif any(phrase in sentence_lower for phrase in ["inhala por 4", "inhale for 4", "breathe in for 4"]):
        return {
            "type": "box_breathing",
            "phase": "inhale"
        }
    elif any(phrase in sentence_lower for phrase in ["mantén por 4", "hold for 4", "hold your breath for 4"]):
        return {
            "type": "box_breathing",
            "phase": "hold_in"
        }
    elif any(phrase in sentence_lower for phrase in ["exhala por 4", "exhale for 4", "breathe out for 4"]):
        return {
            "type": "box_breathing",
            "phase": "exhale"
        }
    
    # Deep breathing pattern
    elif any(phrase in sentence_lower for phrase in ["respiración profunda", "deep breath", "deep breathing"]):
        return {
            "type": "deep_breathing",
            "phase": "inhale"
        }
    
    return None 