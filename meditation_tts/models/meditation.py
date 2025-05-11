"""
Meditation-related data models for the TTS system.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class MeditationScript(BaseModel):
    """Raw meditation script text with structured sections."""
    content: str
    sections: List[Dict[str, str]] = Field(
        description="Identified sections of the meditation (intro, body, guidance, closing, etc.)"
    )

class ProsodyRequest(BaseModel):
    """Input request for the prosody system."""
    emotional_state: str
    meditation_style: str
    meditation_theme: str
    duration_minutes: int
    voice_type: str
    language_code: str
    soundscape: str 