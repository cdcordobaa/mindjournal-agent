"""
LangGraph workflow configuration for the meditation TTS system.
"""

from langgraph.graph import StateGraph, END

from meditation_tts.config.constants import WORKFLOW_STEPS
from meditation_tts.models.state import GraphState
from meditation_tts.workflow.nodes import (
    generate_meditation_script,
    analyze_prosody_needs,
    generate_prosody_profile,
    generate_ssml,
    review_and_improve_ssml,
    generate_meditation_audio,
    mix_with_soundscape
)

def create_workflow_graph() -> StateGraph:
    """
    Create the workflow graph for the meditation TTS system.
    
    Returns:
        StateGraph: The configured workflow graph
    """
    # Create workflow graph
    workflow = StateGraph(GraphState)
    
    # Add all nodes
    workflow.add_node("generate_script", generate_meditation_script)
    workflow.add_node("analyze_prosody", analyze_prosody_needs)
    workflow.add_node("create_profile", generate_prosody_profile)
    workflow.add_node("generate_ssml", generate_ssml)
    workflow.add_node("review_and_improve_ssml", review_and_improve_ssml)
    workflow.add_node("generate_audio", generate_meditation_audio)
    workflow.add_node("mix_audio", mix_with_soundscape)
    
    # Configure the workflow edges
    workflow.add_edge("generate_script", "analyze_prosody")
    workflow.add_edge("analyze_prosody", "create_profile")
    workflow.add_edge("create_profile", "generate_ssml")
    workflow.add_edge("generate_ssml", "review_and_improve_ssml")
    workflow.add_edge("review_and_improve_ssml", "generate_audio")
    workflow.add_edge("generate_audio", "mix_audio")
    workflow.add_edge("mix_audio", END)
    
    # Set entry point
    workflow.set_entry_point(WORKFLOW_STEPS[0])
    
    return workflow 