#!/usr/bin/env python3
"""
Test script for the integrated meditation generation workflow.
"""

import os
import json
import argparse
from dotenv import load_dotenv
from src.integrated_workflow import run_meditation_generation, WORKFLOW_STEPS, EmotionalState, MeditationStyle, MeditationTheme, VoiceType, SoundscapeType
import time
import datetime

def validate_and_fix_ssml(ssml):
    """Validate SSML and fix common issues like unbalanced tags"""
    import re
    
    print("Validating SSML structure...")
    
    # Track tag counts
    open_tags = re.findall(r'<([^/\s>]+)(?:\s[^>]*)?>', ssml)
    close_tags = re.findall(r'</([^>]+)>', ssml)
    
    # Count of each tag type
    open_counts = {}
    close_counts = {}
    
    for tag in open_tags:
        open_counts[tag] = open_counts.get(tag, 0) + 1
    
    for tag in close_tags:
        close_counts[tag] = close_counts.get(tag, 0) + 1
    
    # Check for unbalanced tags
    unbalanced = False
    for tag in set(list(open_counts.keys()) + list(close_counts.keys())):
        if tag in ['break']:  # Self-closing tags
            continue
            
        open_count = open_counts.get(tag, 0)
        close_count = close_counts.get(tag, 0)
        
        if open_count != close_count:
            print(f"Warning: Unbalanced {tag} tags. {open_count} opening tags and {close_count} closing tags.")
            unbalanced = True
    
    if unbalanced:
        print("Fixing unbalanced tags...")
        
        # Fix approach 1: Balance p tags properly
        if 'p' in open_counts and open_counts.get('p', 0) > close_counts.get('p', 0):
            # Insert missing </p> tags at appropriate positions
            # Find all places where a </p> should be but is missing
            pattern = r'(<p>(?:(?!</p>).)*?)(?=<p>|<break|</speak>)'
            ssml = re.sub(pattern, r'\1</p>', ssml, flags=re.DOTALL)
        
        # Fix approach 2: Balance s tags
        if 's' in open_counts and open_counts.get('s', 0) > close_counts.get('s', 0):
            # Insert missing </s> tags
            pattern = r'(<s>(?:(?!</s>).)*?)(?=<s>|</p>|<p>|<break|</speak>)'
            ssml = re.sub(pattern, r'\1</s>', ssml, flags=re.DOTALL)
        
        # Fix approach 3: Balance prosody tags
        if 'prosody' in open_counts and open_counts.get('prosody', 0) > close_counts.get('prosody', 0):
            # This is more complex as prosody tags can be nested
            # For simplicity, let's just add closing tags at the end of paragraphs
            pattern = r'(</p>)'
            replacement = r'</prosody>\1'
            # Only add as many as we need
            diff = open_counts.get('prosody', 0) - close_counts.get('prosody', 0)
            ssml = re.sub(pattern, replacement, ssml, count=diff)
        
        # Final validation
        open_tags = re.findall(r'<([^/\s>]+)(?:\s[^>]*)?>', ssml)
        close_tags = re.findall(r'</([^>]+)>', ssml)
        
        open_counts = {}
        close_counts = {}
        
        for tag in open_tags:
            open_counts[tag] = open_counts.get(tag, 0) + 1
        
        for tag in close_tags:
            close_counts[tag] = close_counts.get(tag, 0) + 1
        
        all_balanced = True
        for tag in set(list(open_counts.keys()) + list(close_counts.keys())):
            if tag in ['break']:  # Self-closing tags
                continue
                
            open_count = open_counts.get(tag, 0)
            close_count = close_counts.get(tag, 0)
            
            if open_count != close_count:
                print(f"Warning: Still have unbalanced {tag} tags after fixing. {open_count} opening tags and {close_count} closing tags.")
                all_balanced = False
        
        if all_balanced:
            print("All tags balanced successfully!")
    else:
        print("SSML structure is valid. All tags are balanced.")
        
    return ssml

def main():
    # Load environment variables
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test the meditation generation workflow')
    parser.add_argument('--start-step', choices=WORKFLOW_STEPS, help='Start from a specific workflow step')
    parser.add_argument('--no-audio', action='store_true', help='Skip audio generation and mixing steps')
    parser.add_argument('--skip-ssml-review', action='store_true', help='Skip the SSML review step')
    parser.add_argument('--aws-login', action='store_true', help='Perform AWS SSO login before running')
    args = parser.parse_args()
    
    # Perform AWS SSO login if requested
    if args.aws_login:
        try:
            import subprocess
            import sys
            
            print("Performing AWS SSO login...")
            
            # Get AWS profile from environment or use default
            aws_profile = os.environ.get('AWS_PROFILE', 'default')
            print(f"Using AWS profile: {aws_profile}")
            
            # Run the SSO login command
            result = subprocess.run(
                ["aws", "sso", "login", "--profile", aws_profile],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("AWS SSO login successful")
            else:
                print(f"AWS SSO login failed with error: {result.stderr}")
                print("Continuing with workflow, but AWS services may fail")
        except Exception as e:
            print(f"AWS SSO login failed with exception: {str(e)}")
            print("Continuing with workflow, but AWS services may fail")
    
    # Create the request
    request = {
        "user_id": "test_user",
        "request_id": "test_request",
        "meditation_style": MeditationStyle.MINDFULNESS.value,
        "meditation_theme": MeditationTheme.STRESS_RELIEF.value,  
        "emotional_state": EmotionalState.ANXIOUS.value,
        "duration_minutes": 5,
        "voice_type": VoiceType.FEMALE.value,
        "soundscape_type": SoundscapeType.NATURE.value,
        "language_code": "en-US"
    }
    
    print(f"Testing meditation workflow with request: {json.dumps(request, indent=2)}")
    
    # Determine end step based on flags
    end_step = None
    if args.no_audio:
        if args.skip_ssml_review:
            end_step = "generate_ssml"
        else:
            end_step = "review_and_improve_ssml"
    
    # Run the workflow
    start_time = time.time()
    result = run_meditation_generation(request, start_step=args.start_step, end_step=end_step)
    end_time = time.time()
    
    print(f"\nWorkflow completed in {end_time - start_time:.2f} seconds")
    
    # Save the script output to a file for inspection
    if result.get("meditation_script"):
        script_content = result["meditation_script"].get("content") if isinstance(result["meditation_script"], dict) else result["meditation_script"]
        with open(f"output/script_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
            f.write(script_content)
            print(f"Script saved to {f.name}")

    # Save the SSML output to a file for inspection
    if result.get("ssml_output"):
        # Validate and fix the SSML
        fixed_ssml = validate_and_fix_ssml(result["ssml_output"])
        
        # Save the fixed SSML
        ssml_filename = f"output/ssml_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(ssml_filename, "w") as f:
            f.write(fixed_ssml)
            print(f"SSML saved to {ssml_filename}")
            
        # Show SSML review results if available
        if "ssml_review" in result:
            print("\nSSML Review Results:")
            print(f"Review iterations: {result['ssml_review']['iterations']}")
            for issue in result['ssml_review']['issues_fixed']:
                print(f"- {issue}")
    
    print("\nOutput files can be found in the output directory")
    print(result)
    return result

if __name__ == "__main__":
    exit(main()) 