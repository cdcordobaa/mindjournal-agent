"""
Workflow runner for executing the meditation TTS workflow.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from meditation_tts.config.constants import WORKFLOW_STEPS, JSON_OUTPUT_DIR
from meditation_tts.models.state import GraphState
from meditation_tts.utils.state_utils import save_state, load_state, get_latest_state_file
from meditation_tts.utils.logging_utils import log_state_transition, logger
from meditation_tts.workflow.graph import create_workflow_graph
from meditation_tts.workflow.nodes import (
    generate_meditation_script,
    analyze_prosody_needs,
    generate_prosody_profile,
    generate_ssml,
    review_and_improve_ssml,
    generate_meditation_audio,
    mix_with_soundscape
)

def run_workflow_step(step: str, state: Optional[GraphState] = None) -> GraphState:
    """
    Run a single step of the workflow.
    
    Args:
        step: The workflow step to run
        state: Optional state to use (otherwise load from previous step)
        
    Returns:
        GraphState: The updated state after running the step
        
    Raises:
        ValueError: If the step is invalid
    """
    logger.info(f"Running workflow step: {step}")
    
    if step not in WORKFLOW_STEPS:
        error_msg = f"Invalid step: {step}. Must be one of {WORKFLOW_STEPS}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Load state if not provided
    if state is None:
        # Try to load the latest state from the previous step
        prev_step_idx = WORKFLOW_STEPS.index(step) - 1
        if prev_step_idx >= 0:
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            state_file = get_latest_state_file(prev_step)
            if state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {state_file})")
                state = load_state(state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from {state_file}")
            else:
                logger.warning(f"No state file found for previous step: {prev_step}")
    
    # Initialize new state if needed
    if state is None:
        state = {
            "request": {},
            "meditation_script": None,
            "prosody_analysis": None,
            "prosody_profile": None,
            "ssml_output": None,
            "audio_output": None,
            "error": None,
            "current_step": step
        }
    
    # Log the state before running
    logger.info(f"State before workflow step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
    
    # Create workflow graph
    workflow = create_workflow_graph()
    
    # Set entry point to specified step
    workflow.set_entry_point(step)
    
    # Compile and run
    compiled_workflow = workflow.compile()
    logger.info(f"Invoking workflow at step: {step}")
    result = compiled_workflow.invoke(state)
    
    # Save state after step completion
    state_file = save_state(result, step)
    logger.info(f"Saved state to: {state_file}")
    
    return result

def run_single_step(step: str, state: GraphState) -> GraphState:
    """
    Run a single step of the workflow without chaining to the next step.
    
    Args:
        step: The workflow step to run
        state: The current state
        
    Returns:
        GraphState: The updated state after running the step
    """
    logger.info(f"Running single step: {step}")
    
    # Map steps to functions
    step_functions = {
        "generate_script": generate_meditation_script,
        "analyze_prosody": analyze_prosody_needs,
        "create_profile": generate_prosody_profile,
        "generate_ssml": generate_ssml,
        "review_and_improve_ssml": review_and_improve_ssml,
        "generate_audio": generate_meditation_audio,
        "mix_audio": mix_with_soundscape
    }
    
    # Log state before running
    logger.info(f"State before single step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
    
    # Run the step
    if step in step_functions:
        state = step_functions[step](state)
        save_state_path = save_state(state, step)
        logger.info(f"Saved state after step {step} to: {save_state_path}")
        
        # Log state after running
        logger.info(f"State after single step {step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
        
        return state
    else:
        state["error"] = f"Unknown step: {step}"
        return state

def run_meditation_generation(request_data: Dict[str, Any], 
                          start_step: Optional[str] = None, 
                          end_step: Optional[str] = None,
                          initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run the meditation generation process, optionally starting from a specific step.
    
    Args:
        request_data: The request parameters for meditation generation
        start_step: Optional step to start from (default is first step)
        end_step: Optional step to end at (default is the last step)
        initial_state: Optional initial state (used when resuming from a saved state)
        
    Returns:
        Dict[str, Any]: The result state after workflow completion
    """
    logger.info(f"Starting meditation generation process from step: {start_step or WORKFLOW_STEPS[0]}")
    if end_step:
        logger.info(f"Will stop after step: {end_step}")
    logger.info(f"Request: {json.dumps(request_data)}")
    
    # Custom workflow based on start_step and end_step
    if end_step and end_step in WORKFLOW_STEPS:
        # Find the indices of the start and end steps
        start_idx = WORKFLOW_STEPS.index(start_step) if start_step and start_step in WORKFLOW_STEPS else 0
        end_idx = WORKFLOW_STEPS.index(end_step)
        
        # Create a list of steps to run
        steps_to_run = WORKFLOW_STEPS[start_idx:end_idx+1]
        logger.info(f"Running steps: {steps_to_run}")
        
        # Use provided initial state or try to load from previous step
        state = initial_state
        if state is None and start_step and start_step in WORKFLOW_STEPS and WORKFLOW_STEPS.index(start_step) > 0:
            prev_step_idx = WORKFLOW_STEPS.index(start_step) - 1
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            prev_state_file = get_latest_state_file(prev_step)
            
            if prev_state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {prev_state_file})")
                state = load_state(prev_state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from previous step: {prev_step}")
        
        # Initialize state if not loaded from previous step or provided
        if state is None:
            state = {
                "request": request_data,
                "meditation_script": None,
                "prosody_analysis": None,
                "prosody_profile": None,
                "ssml_output": None,
                "audio_output": None,
                "error": None,
                "current_step": steps_to_run[0]
            }
        else:
            # Update request data in loaded state
            state["request"] = request_data
            state["current_step"] = steps_to_run[0]
            
            # Clear error to allow rerunning after an error
            if "error" in state:
                state["error"] = None
        
        # Run each step sequentially
        for step in steps_to_run:
            state["current_step"] = step
            logger.info(f"Running step: {step}")
            logger.info(f"State before step: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
            state = run_single_step(step, state)
            if state.get("error"):
                logger.error(f"Error in step {step}: {state.get('error')}")
                return state
        
        return state
    elif start_step and start_step in WORKFLOW_STEPS:
        # Traditional flow from start_step
        # Use provided initial state or try to load from previous step
        state = initial_state
        if state is None and WORKFLOW_STEPS.index(start_step) > 0:
            prev_step_idx = WORKFLOW_STEPS.index(start_step) - 1
            prev_step = WORKFLOW_STEPS[prev_step_idx]
            prev_state_file = get_latest_state_file(prev_step)
            
            if prev_state_file:
                logger.info(f"Loading state from previous step: {prev_step} (file: {prev_state_file})")
                state = load_state(prev_state_file)
                if state:
                    logger.info(f"Successfully loaded state from previous step: {prev_step}")
                else:
                    logger.warning(f"Failed to load state from previous step: {prev_step}")
        
        # Initialize state if not loaded or provided
        if state is None:
            state = {
                "request": request_data,
                "meditation_script": None,
                "prosody_analysis": None,
                "prosody_profile": None,
                "ssml_output": None,
                "audio_output": None,
                "error": None,
                "current_step": start_step
            }
        else:
            # Update request data in loaded state
            state["request"] = request_data
            state["current_step"] = start_step
            
            # Clear error to allow rerunning after an error
            if "error" in state:
                state["error"] = None
            
        # Log what's in the state before running
        logger.info(f"State before running step {start_step}: {json.dumps({k: 'Present' if v is not None else 'None' for k, v in state.items()})}")
        
        return run_workflow_step(start_step, state)
    else:
        # Full workflow from beginning
        state = initial_state or {
            "request": request_data,
            "meditation_script": None,
            "prosody_analysis": None,
            "prosody_profile": None,
            "ssml_output": None,
            "audio_output": None,
            "error": None,
            "current_step": WORKFLOW_STEPS[0]
        }
        return run_workflow_step(WORKFLOW_STEPS[0], state)