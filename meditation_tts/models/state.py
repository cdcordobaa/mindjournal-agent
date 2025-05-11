"""
State models for workflow state management.
"""

from typing import Dict, List, Optional, Any, TypedDict

class GraphState(TypedDict, total=False):
    """
    The state object that will be passed between nodes in the LangGraph.
    Total=False allows for partial initialization of the state.
    """
    request: Dict[str, Any]
    meditation_script: Optional[Dict[str, Any]]
    prosody_analysis: Optional[Dict[str, Any]]
    prosody_profile: Optional[Dict[str, Any]]
    ssml_output: Optional[str]
    audio_output: Optional[Dict[str, Any]]
    error: Optional[str]
    current_step: Optional[str] 