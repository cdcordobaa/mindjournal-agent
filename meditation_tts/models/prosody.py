"""
Prosody-related data models for the TTS system.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PitchProfile(BaseModel):
    """Profile for pitch adjustments in speech synthesis."""
    base_pitch: str = Field(description="Base pitch adjustment, e.g. '-10%', 'low'")
    range: str = Field(description="Pitch range/variation, e.g. '+20%', 'wide'")
    contour_pattern: str = Field(description="Natural pitch contour description")
    emotional_contours: Dict[str, str] = Field(
        description="Pitch contours for different emotional states",
        default_factory=lambda: {
            "calm": "gradual downward drift with gentle rises",
            "anxious": "higher baseline with more variation",
            "energetic": "higher baseline with upward contours",
            "tired": "lower baseline with minimal variation",
            "happy": "moderate baseline with upward contours",
            "sad": "lower baseline with downward contours",
            "stressed": "higher baseline with tense contours"
        }
    )

class RateProfile(BaseModel):
    """Profile for speech rate adjustments in speech synthesis."""
    base_rate: str = Field(description="Base speaking rate, e.g. '90%', 'slow'")
    variation: str = Field(description="Rate variation pattern")
    special_sections: Dict[str, str] = Field(
        description="Rate adjustments for special sections",
        default_factory=lambda: {
            "breathing": "70%",
            "introduction": "80%",
            "closing": "75%",
            "grounding": "65%",
            "body_scan": "60%",
            "affirmations": "75%",
            "visualization": "70%"
        }
    )
    emotional_rates: Dict[str, str] = Field(
        description="Rate adjustments for different emotional states",
        default_factory=lambda: {
            "calm": "70%",
            "anxious": "85%",
            "energetic": "90%",
            "tired": "65%",
            "happy": "85%",
            "sad": "70%",
            "stressed": "80%"
        }
    )

class PauseProfile(BaseModel):
    """Profile for pause durations in speech synthesis."""
    short_pause: str = Field(description="Duration for short pauses, e.g. '500ms'")
    medium_pause: str = Field(description="Duration for medium pauses, e.g. '1s'")
    long_pause: str = Field(description="Duration for long pauses, e.g. '3s'")
    breath_pause: str = Field(description="Duration for breathing instruction pauses, e.g. '4s'")
    sentence_pattern: str = Field(description="Pattern for sentence pauses")
    breathing_patterns: Dict[str, Dict[str, str]] = Field(
        description="Pause patterns for different breathing techniques",
        default_factory=lambda: {
            "4-7-8": {
                "inhale": "4s",
                "hold": "7s",
                "exhale": "8s"
            },
            "box_breathing": {
                "inhale": "4s",
                "hold_in": "4s",
                "exhale": "4s",
                "hold_out": "4s"
            },
            "deep_breathing": {
                "inhale": "4s",
                "exhale": "6s"
            }
        }
    )

class EmphasisProfile(BaseModel):
    """Profile for word emphasis in speech synthesis."""
    intensity: str = Field(description="Overall emphasis intensity")
    key_terms: List[str] = Field(description="Terms to emphasize")
    emotional_emphasis: Dict[str, str] = Field(
        description="Emphasis patterns for different emotional states",
        default_factory=lambda: {
            "calm": "reduced",
            "anxious": "moderate",
            "energetic": "strong",
            "tired": "reduced",
            "happy": "moderate",
            "sad": "reduced",
            "stressed": "moderate"
        }
    )

class ProsodyProfile(BaseModel):
    """Complete prosody profile for a specific emotional state and meditation context."""
    pitch: PitchProfile
    rate: RateProfile
    pauses: PauseProfile
    emphasis: EmphasisProfile
    volume: str = Field(description="Overall volume setting, e.g. 'soft', 'medium', '+5dB'")
    voice_quality: Optional[str] = Field(default=None, description="Voice quality hint if supported")
    
    # Section-specific profiles
    section_profiles: Dict[str, Dict[str, str]] = Field(
        description="Detailed profiles for different section types",
        default_factory=lambda: {
            "introduction": {
                "pitch": "-15%",
                "rate": "80%",
                "volume": "soft"
            },
            "grounding": {
                "pitch": "-20%",
                "rate": "65%",
                "volume": "x-soft"
            },
            "body_scan": {
                "pitch": "-18%",
                "rate": "60%",
                "volume": "x-soft"
            },
            "breathing": {
                "pitch": "-15%",
                "rate": "70%",
                "volume": "soft"
            },
            "visualization": {
                "pitch": "-12%",
                "rate": "75%",
                "volume": "soft"
            },
            "affirmations": {
                "pitch": "-10%",
                "rate": "75%",
                "volume": "medium"
            },
            "closing": {
                "pitch": "-15%",
                "rate": "75%",
                "volume": "soft"
            }
        }
    )
    
    # Language-specific adjustments
    language_adjustments: Dict[str, Dict[str, str]] = Field(
        description="Adjustments specific to each language code",
        default_factory=lambda: {
            "es-ES": {
                "rate": "80%",
                "pitch": "-12%",
                "volume": "soft"
            },
            "en-US": {
                "rate": "85%",
                "pitch": "-10%",
                "volume": "medium"
            }
        }
    )
    
    # Progressive changes throughout the meditation
    progression: Dict[str, Dict[str, str]] = Field(
        description="How prosody changes throughout the meditation",
        default_factory=lambda: {
            "start": {
                "rate": "85%",
                "pitch": "-10%",
                "volume": "medium"
            },
            "middle": {
                "rate": "75%",
                "pitch": "-15%",
                "volume": "soft"
            },
            "end": {
                "rate": "70%",
                "pitch": "-20%",
                "volume": "x-soft"
            }
        }
    )

class ProsodyAnalysis(BaseModel):
    """Analysis of prosody needs for the specific meditation."""
    overall_tone: str
    key_terms: List[str]
    breathing_patterns: List[Dict[str, str]]
    recommended_emphasis_points: List[Dict[str, str]]
    section_characteristics: Dict[str, str] 