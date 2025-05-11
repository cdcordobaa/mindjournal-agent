"""
Meditation TTS System - Generate meditation audio with advanced prosody control.
"""

from meditation_tts.main import (
    create_test_request,
    run_prosody_generation
)

from meditation_tts.models.enums import (
    EmotionalState,
    MeditationStyle,
    MeditationTheme,
    VoiceType,
    SoundscapeType
)

__version__ = "0.1.0"
__all__ = [
    'create_test_request',
    'run_prosody_generation',
    'EmotionalState',
    'MeditationStyle',
    'MeditationTheme',
    'VoiceType',
    'SoundscapeType'
]
