#!/usr/bin/env python3
import json
import os
import argparse
from datetime import datetime
from typing import Dict, Any, List

def generate_meditation_script(emotional_state: str, 
                              duration_minutes: int = 10, 
                              meditation_style: str = "Mindfulness",
                              meditation_theme: str = "StressRelief",
                              voice_type: str = "Female",
                              language_code: str = "en-US",
                              soundscape: str = "Nature") -> Dict[str, Any]:
    """
    Generate a meditation script based on input parameters.
    
    This is a simplified implementation - in a real-world scenario, 
    this would likely use an LLM or a template system.
    
    Args:
        emotional_state: Current emotional state (e.g., anxious, sad, tired)
        duration_minutes: Duration of meditation in minutes
        meditation_style: Style of meditation (e.g., Mindfulness, Guided, Body Scan)
        meditation_theme: Theme of meditation (e.g., StressRelief, Sleep, Focus)
        voice_type: Type of voice (Male, Female, Neutral)
        language_code: Language code (e.g., en-US)
        soundscape: Background sound theme (e.g., Nature, Ocean, Rain)
        
    Returns:
        Dict with meditation request and script
    """
    # Create request object
    request = {
        "emotional_state": emotional_state.lower(),
        "meditation_style": meditation_style,
        "meditation_theme": meditation_theme,
        "duration_minutes": duration_minutes,
        "voice_type": voice_type,
        "language_code": language_code,
        "soundscape": soundscape
    }
    
    # Simple template-based approach for demonstration
    introduction_text = f"Introduction (Duration: 2 minutes)\n\nWelcome to this {duration_minutes}-minute {meditation_style} meditation focused on {meditation_theme}. I'll guide you through this journey to help you with your {emotional_state} feelings and find a space of calm in your day.\n\n(20 seconds of silence to prepare)"
    
    main_instructions = f"Main Instructions (Duration: 2 minutes)\n\nPlease find a comfortable place to sit or lie down. Close your eyes and try to relax your body. Feel the weight of your body on the seat or on the floor.\n\n(30 seconds of silence)"
    
    breathing_section = f"Breathing Section (Duration: 3 minutes)\n\nNow, let's focus on the breath. Inhale slowly counting to four...hold the breath for two seconds... exhale slowly counting to six.\n\n(20 seconds of silence)\n\nRepeat this cycle several times. Each time you inhale, imagine filling your body with calm and peace. Each time you exhale, visualize releasing any stress or {emotional_state} feelings you might be experiencing.\n\n(1 minute of silence for breathing practice)\n\nContinue breathing this way, and if you find it difficult, simply return to your natural breath.\n\n(1 minute of silence)"
    
    continuation = f"Continuation of Main Guide (Duration: 2 minutes)\n\nAs you continue breathing, allow your attention to center on the present. If you notice your mind starting to wander, simply return to your breath.\n\n(30 seconds of silence)\n\nImagine that each thought that appears is like a leaf floating on a river. You don't need to interact with it, simply let it pass by and return your attention to your breath.\n\n(30 seconds of silence)"
    
    closing = f"Closing (Duration: 1 minute)\n\nNow, little by little, start moving your fingers and toes. When you feel ready, slowly open your eyes. Remember that you can return to this place of calm and peace whenever you need it.\n\nThank you for taking this time for yourself. I hope you feel a bit more relaxed and at peace."
    
    # Combine sections
    content = f"{introduction_text}\n\n{main_instructions}\n\n{breathing_section}\n\n{continuation}\n\n{closing}"
    
    # Create sections list for structured content
    sections = [
        {"type": "introduction", "content": "Introduction (Duration: 2 minutes)"},
        {"type": "body", "content": f"Welcome to this {duration_minutes}-minute {meditation_style} meditation focused on {meditation_theme}. I'll guide you through this journey to help you with your {emotional_state} feelings and find a space of calm in your day."},
        {"type": "body", "content": "(20 seconds of silence to prepare)"},
        {"type": "body", "content": "Main Instructions (Duration: 2 minutes)"},
        {"type": "body", "content": "Please find a comfortable place to sit or lie down. Close your eyes and try to relax your body. Feel the weight of your body on the seat or on the floor."},
        {"type": "body", "content": "(30 seconds of silence)"},
        {"type": "breathing", "content": "Breathing Section (Duration: 3 minutes)"},
        {"type": "breathing", "content": "Now, let's focus on the breath. Inhale slowly counting to four...hold the breath for two seconds... exhale slowly counting to six."},
        {"type": "body", "content": "(20 seconds of silence)"},
        {"type": "body", "content": f"Repeat this cycle several times. Each time you inhale, imagine filling your body with calm and peace. Each time you exhale, visualize releasing any stress or {emotional_state} feelings you might be experiencing."},
        {"type": "breathing", "content": "(1 minute of silence for breathing practice)"},
        {"type": "breathing", "content": "Continue breathing this way, and if you find it difficult, simply return to your natural breath."},
        {"type": "body", "content": "(1 minute of silence)"},
        {"type": "body", "content": "Continuation of Main Guide (Duration: 2 minutes)"},
        {"type": "breathing", "content": "As you continue breathing, allow your attention to center on the present. If you notice your mind starting to wander, simply return to your breath."},
        {"type": "body", "content": "(30 seconds of silence)"},
        {"type": "breathing", "content": "Imagine that each thought that appears is like a leaf floating on a river. You don't need to interact with it, simply let it pass by and return your attention to your breath."},
        {"type": "body", "content": "(30 seconds of silence)"},
        {"type": "body", "content": "Closing (Duration: 1 minute)"},
        {"type": "body", "content": "Now, little by little, start moving your fingers and toes. When you feel ready, slowly open your eyes. Remember that you can return to this place of calm and peace whenever you need it."},
        {"type": "closing", "content": "Thank you for taking this time for yourself. I hope you feel a bit more relaxed and at peace."}
    ]
    
    # Generate SSML with appropriate prosody
    ssml_output = generate_ssml(sections, emotional_state, language_code)
    
    # Assemble final output
    return {
        "request": request,
        "meditation_script": {
            "content": content,
            "sections": sections
        },
        "ssml_output": ssml_output,
        "error": None
    }

def generate_ssml(sections: List[Dict[str, str]], emotional_state: str, language_code: str) -> str:
    """
    Generate SSML markup with appropriate prosody settings.
    
    Args:
        sections: List of meditation script sections
        emotional_state: Emotional state being addressed
        language_code: Language code
        
    Returns:
        SSML formatted text
    """
    # Default prosody settings
    base_rate = "85%"
    base_pitch = "-10%"
    intro_rate = "80%"
    intro_pitch = "-15%"
    breathing_rate = "70%"
    closing_rate = "75%"
    closing_pitch = "-15%"
    volume = "soft"
    
    # Adjust for different emotional states
    if emotional_state.lower() == "anxious":
        base_rate = "82%"  # Slightly slower for anxious people
        base_pitch = "-12%"  # Slightly lower pitch for calming effect
    elif emotional_state.lower() == "sad":
        base_rate = "87%"  # Slightly faster for sad people
        base_pitch = "-8%"  # Slightly higher pitch for uplifting effect
    elif emotional_state.lower() == "tired":
        base_rate = "88%"  # Faster for tired people to maintain attention
        base_pitch = "-8%"  # Higher pitch to keep engaged
    
    # Key terms for emphasis
    key_terms = [
        "breath", "breathing", "inhale", "exhale", 
        "calm", "peace", "present", "attention", 
        "stress", "anxiety", "mind", "thought",
        "relax", "comfortable", emotional_state
    ]
    
    # Build SSML
    ssml = "<speak>\n"
    
    for section in sections:
        # Set prosody based on section type
        if "introduction" in section["type"]:
            ssml += f'<prosody rate="{intro_rate}" pitch="{intro_pitch}" volume="{volume}">\n'
        elif "breathing" in section["type"]:
            ssml += f'<prosody rate="{breathing_rate}" pitch="{base_pitch}" volume="{volume}">\n'
        elif "closing" in section["type"]:
            ssml += f'<prosody rate="{closing_rate}" pitch="{closing_pitch}" volume="{volume}">\n'
        else:
            ssml += f'<prosody rate="{base_rate}" pitch="{base_pitch}" volume="{volume}">\n'
        
        # Process content with emphasis for key terms
        content = section["content"]
        for term in key_terms:
            # Only emphasize whole words, not parts of words
            content = content.replace(f" {term} ", f" <emphasis level=\"moderate\">{term}</emphasis> ")
            content = content.replace(f" {term}.", f" <emphasis level=\"moderate\">{term}</emphasis>.")
            content = content.replace(f" {term},", f" <emphasis level=\"moderate\">{term}</emphasis>,")
        
        ssml += content + "\n</prosody>\n\n"
        
        # Add appropriate pauses
        if "silence" in content:
            ssml += '<break time="4s"/>\n\n'
        else:
            ssml += '<break time="800ms"/>\n\n'
    
    ssml += "</speak>"
    return ssml

def main():
    parser = argparse.ArgumentParser(description='Generate a meditation script')
    parser.add_argument('--emotional_state', required=True, help='Current emotional state (e.g., anxious, sad, tired)')
    parser.add_argument('--duration', type=int, default=10, help='Duration in minutes')
    parser.add_argument('--style', default='Mindfulness', help='Meditation style')
    parser.add_argument('--theme', default='StressRelief', help='Meditation theme')
    parser.add_argument('--voice', default='Female', choices=['Male', 'Female', 'Neutral'], help='Voice type')
    parser.add_argument('--language', default='en-US', help='Language code')
    parser.add_argument('--soundscape', default='Nature', help='Background soundscape')
    parser.add_argument('--output_dir', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Generate meditation script
    meditation = generate_meditation_script(
        emotional_state=args.emotional_state,
        duration_minutes=args.duration,
        meditation_style=args.style,
        meditation_theme=args.theme,
        voice_type=args.voice,
        language_code=args.language,
        soundscape=args.soundscape
    )
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{args.output_dir}/meditation_{args.emotional_state}_{args.theme}_{timestamp}.json"
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(meditation, f, indent=2, ensure_ascii=False)
    
    print(f"Meditation script generated and saved to {filename}")
    print("To generate audio, run:")
    print(f"python generate_meditation_audio.py {filename}")

if __name__ == "__main__":
    main() 