"""
SSML review and improvement node for the workflow.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from meditation_tts.models.state import GraphState
from meditation_tts.utils.logging_utils import log_state_transition, log_llm_interaction, logger

def review_and_improve_ssml(state: GraphState) -> GraphState:
    """
    Review generated SSML for issues and improve it according to best practices.
    
    Args:
        state: The current workflow state
        
    Returns:
        GraphState: The updated workflow state with improved SSML
    """
    try:
        logger.info("Starting SSML review and improvement")
        log_state_transition("review_and_improve_ssml", state)
        
        if "error" in state and state["error"]:
            logger.error(f"Skipping due to previous error: {state['error']}")
            return state
            
        if not state.get("ssml_output"):
            state["error"] = "No SSML output to review"
            return state
            
        # Get the current SSML
        ssml = state["ssml_output"]
        
        # Initialize LLM for review
        llm = ChatOpenAI(temperature=0.2, model="gpt-4o")
        
        # Create system prompt with SSML best practices knowledge
        system_prompt = """You are an expert SSML reviewer and fixer specializing in meditation audio. Your task is to analyze SSML markup, identify and fix any issues, particularly for AWS Polly Neural voices used in meditation applications.

When reviewing SSML, focus first on technical correctness:

1. Technical Correctness (HIGHEST PRIORITY):
   - Fix any unbalanced tags (unclosed <prosody>, <p>, or <s> tags)
   - Fix duplicate closing tags or incorrect nesting order
   - Fix improper value formats (e.g., missing % symbol in percentages)
   - Fix missing units in <break> durations (should use "ms" or "s")
   - Fix invalid attribute values (e.g., outside supported ranges)
   - Ensure compatibility with AWS Polly Neural voices

2. Tag compatibility with Neural voices:
   - Neural voices support: <speak>, <break>, <prosody>, <p>, <s>, <say-as>, <phoneme>, <w>, <lang>, <mark>, <sub>
   - Neural voices DO NOT support: <emphasis>, <amazon:auto-breaths>, <amazon:effect name="whispered">, <phonation>
   - Replace unsupported tags with allowed alternatives

3. Meditation-specific best practices:
   - Progressive slowing of rate throughout meditation (<prosody rate> gradually decreasing)
   - Appropriate pause durations after breathing instructions (<break> of 3-6s)
   - Lower pitch for relaxation sections (<prosody pitch> between -10% and -20%)
   - Softer volume for deeper sections (<prosody volume> using "soft" or "x-soft")
   - Proper pacing for body scan sections (slower rate, longer breaks)

Provide a corrected and improved version of the SSML that maintains the meditation's content and intent while ensuring technical correctness."""

        # Iterative improvement cycle
        max_iterations = 3
        iteration_count = 0
        issues_fixed = []
        
        while iteration_count < max_iterations:
            iteration_count += 1
            logger.info(f"Starting SSML review iteration {iteration_count}")
            
            # Create review prompt with current SSML
            review_prompt = f"""Review and fix the following SSML for a meditation:

```xml
{ssml}
```

Focus on these priorities in order:
1. Technical correctness - Fix ALL unbalanced tags, nesting issues, or invalid values (CRITICAL)
2. AWS Polly Neural voice compatibility - Replace any unsupported tags
3. Meditation experience enhancement - Improve pacing, prosody, pauses

If you find technical issues, fix them ALL and provide a complete corrected SSML.
If there are no technical issues but you find opportunities to enhance the meditation experience, make those improvements.
If the SSML looks technically correct and well-optimized, state that no improvements are needed.

Return your analysis followed by the complete improved SSML. The SSML MUST be valid XML that can be parsed without errors."""
            
            # Get the review and improved SSML
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=review_prompt)
            ]
            
            logger.info(f"Requesting SSML review iteration {iteration_count}")
            response = llm.invoke(messages)
            
            # Log the review interaction
            log_llm_interaction(
                prompt=review_prompt,
                response_content=response.content,
                model=llm.model_name,
                purpose=f"SSML Review Iteration {iteration_count}"
            )
            
            # Extract the analysis and improved SSML
            content = response.content
            
            # Check if no improvements needed
            if "no improvements are needed" in content.lower() or "ssml looks good" in content.lower():
                logger.info("SSML review complete - No further improvements needed")
                issues_fixed.append(f"Iteration {iteration_count}: No issues found")
                break
                
            # Try to extract improved SSML
            ssml_match = re.search(r'```xml\s*(<speak>.*?</speak>)\s*```', content, re.DOTALL)
            
            if not ssml_match:
                # Try alternative format without code blocks
                ssml_match = re.search(r'<speak>.*?</speak>', content, re.DOTALL)
            
            if ssml_match:
                # Extract issues identified
                analysis_text = content.split("```xml")[0] if "```xml" in content else "Improvements made to SSML"
                issues_fixed.append(f"Iteration {iteration_count}: {analysis_text.strip()}")
                
                # Update the SSML
                improved_ssml = ssml_match.group(1) if "```xml" in content else ssml_match.group(0)
                ssml = improved_ssml
                logger.info(f"SSML updated in iteration {iteration_count}")
            else:
                # If no improved SSML found, make a direct request for valid SSML
                fix_prompt = f"""I need ONLY the complete fixed SSML for the meditation with no explanation. The SSML must be syntactically valid XML with balanced tags and proper nesting.

Original SSML:
{ssml}

Return only the complete SSML, surrounded by <speak> tags."""
                
                fix_response = llm.invoke([HumanMessage(content=fix_prompt)])
                fix_content = fix_response.content
                
                # Try to extract again
                ssml_match = re.search(r'<speak>.*?</speak>', fix_content, re.DOTALL)
                if ssml_match:
                    improved_ssml = ssml_match.group(0)
                    ssml = improved_ssml
                    issues_fixed.append(f"Iteration {iteration_count}: Extracted fixed SSML")
                    logger.info(f"SSML extracted in iteration {iteration_count}")
                else:
                    # Last resort: Simplify the SSML structure completely
                    logger.warning("Could not extract improved SSML, creating simplified version")
                    
                    # Create a simplified but valid SSML document
                    final_fix_prompt = f"""Create a simplified but valid SSML for this meditation text, using only basic paragraph and prosody tags. Return only valid SSML:

Text:
{re.sub(r'<[^>]+>', '', ssml)}"""
                    
                    final_response = llm.invoke([HumanMessage(content=final_fix_prompt)])
                    final_content = final_response.content
                    
                    # Extract one more time
                    final_match = re.search(r'<speak>.*?</speak>', final_content, re.DOTALL)
                    if final_match:
                        ssml = final_match.group(0)
                        issues_fixed.append(f"Iteration {iteration_count}: Created simplified SSML structure")
                        logger.info("Created simplified SSML structure")
                        break
                    else:
                        issues_fixed.append(f"Iteration {iteration_count}: Failed to create valid SSML")
                        logger.error("Failed to create valid SSML")
                        break
        
        # Update the state with the improved SSML
        state["ssml_output"] = ssml
        state["ssml_review"] = {
            "iterations": iteration_count,
            "issues_fixed": issues_fixed
        }
        
        logger.info(f"Completed SSML review after {iteration_count} iterations")
        log_state_transition("review_and_improve_ssml_complete", state)
        return state
        
    except Exception as e:
        logger.exception(f"Error reviewing SSML: {str(e)}")
        state["error"] = f"Error reviewing SSML: {str(e)}"
        return state 