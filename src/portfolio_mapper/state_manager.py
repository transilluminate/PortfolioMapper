# src/portfolio_mapper/state_manager.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
This module centralizes all session state management for the Streamlit app.
"""
import streamlit as st
import uuid

def initialize_session_state():
    """Initializes all required keys in Streamlit's session state."""
    state_defaults = {
        "session_id": str(uuid.uuid4()),
        "processing": False,
        "analysis_result": None,
        "reflection_text": "",
        "anonymisation_confirmed": False,
        "safety_analysis_result": None,
        "pii_warning_acknowledged": False,
        "last_analysis_reflection": None,
        "last_analysis_frameworks": None,
        # Prevents stale on_change callbacks from wiping results
        "analysis_just_completed": False, 
    }
    for key, value in state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def invalidate_results():
    """Callback to clear results when an input changes, forcing re-analysis."""
    # If an analysis was just completed, this callback is likely firing from a stale
    # on_change event. We consume the flag and prevent invalidation for this one run.
    if st.session_state.get("analysis_just_completed", False):
        st.session_state.analysis_just_completed = False
        return

    st.session_state.analysis_result = None
    st.session_state.safety_analysis_result = None
    st.session_state.pii_warning_acknowledged = False
    st.session_state.last_analysis_reflection = None
    st.session_state.last_analysis_frameworks = None

def clear_state():
    """Callback for the 'Clear' button to reset the app state."""
    st.session_state.reflection_text = ""
    st.session_state.processing = False
    st.session_state.anonymisation_confirmed = False
    invalidate_results() # Call invalidate to ensure all results are cleared
