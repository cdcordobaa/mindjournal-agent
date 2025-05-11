"""
Enum definitions for the meditation TTS system.
"""

from enum import Enum

class EmotionalState(str, Enum):
    """Emotional states for meditation context."""
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    CALM = "calm"
    STRESSED = "stressed"
    TIRED = "tired"
    ENERGETIC = "energetic"
    NEUTRAL = "neutral"

class MeditationStyle(str, Enum):
    """Styles of meditation."""
    MINDFULNESS = "Mindfulness"
    GUIDED_IMAGERY = "GuidedImagery"
    BODY_SCAN = "BodyScan"
    LOVING_KINDNESS = "LovingKindness"
    BREATH_FOCUS = "BreathFocus"
    PROGRESSIVE_RELAXATION = "ProgressiveRelaxation"

class MeditationTheme(str, Enum):
    """Themes for meditation content."""
    STRESS_RELIEF = "StressRelief"
    SLEEP = "Sleep"
    FOCUS = "Focus"
    SELF_COMPASSION = "SelfCompassion"
    ANXIETY_RELIEF = "AnxietyRelief"
    CONFIDENCE = "Confidence"
    GRATITUDE = "Gratitude"

class VoiceType(str, Enum):
    """Types of voices for audio generation."""
    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"

class SoundscapeType(str, Enum):
    """Types of background soundscapes."""
    NATURE = "Nature"
    URBAN = "Urban"
    AMBIENT = "Ambient"
    SILENCE = "Silence"
    RAIN = "Rain"
    OCEAN = "Ocean"
    FOREST = "Forest"
    NIGHTTIME = "Nighttime" 