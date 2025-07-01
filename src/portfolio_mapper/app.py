# src/portfolio_mapper/app.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
Main Streamlit application file for the AI-Powered Portfolio Mapper.
This file is responsible for orchestrating the user interface and application flow.
"""
from collections import defaultdict
import streamlit as st
import random

# --- Local Imports ---
from .data_loader import ConfigLoader, FrameworkLoader
from .logic import assemble_analysis_prompt, assemble_safety_prompt
from .llm_functions import call_gemini_for_analysis, call_gemini_for_safety_check
from .analytics import track_event
from .state_manager import initialize_session_state, invalidate_results, clear_state
from .ui_components import (
    render_sidebar, render_main_inputs, render_safety_warnings,
    render_results, render_footer, UserSelections
)
from .models.config import AcademicLevelKey

# set humour level to 100%
LOADING_MESSAGES = [
    "Reticulating splines...",
    "Calibrating the nonsense-o-meter...",
    "Polishing the competency crystals...",
    "Interrogating the reflective neurons...",
    "Aligning the academic chakras...",
    "Defluffing the justification matrix...",
    "Herding the LLM's thought-cats...",
    "Debiasing the digital supervisor...",
    "Synthesising the synergy...",
    "Extrapolating the evidence vector...",
    "Deconstructing the narrative...",
    "Charging the flux capacitor...",
    "Unpacking the Pydantic models...",
    "Warming up the tokeniser...",
    "Pretending to think very hard...",
    "Cross-referencing the rubrics...",
    "Injecting prompt directives...",
    "Validating the validation schema...",
    "Quantifying the qualia...",
]

@st.cache_resource
def load_data():
    """Loads all framework and config files and caches them."""
    try:
        framework_loader = FrameworkLoader(frameworks_dir='frameworks/')
        framework_library = framework_loader.load_all()
        config_loader = ConfigLoader(config_dir='config/')
        config_loader.load_all()
        return framework_library, config_loader
    except Exception as e:
        st.error(f"A critical error occurred during application startup: {e}")
        st.info("Please check the console logs for more details. The application cannot continue.")
        return None, None

def _run_analysis_pipeline(config_loader: ConfigLoader, user_selections: UserSelections):
    """
    Encapsulates the entire multi-stage analysis process.
    Runs safety check, then main analysis if safe.
    """
    # Track the event here, after the UI has updated to show it's processing.
    # This makes the button click feel instantaneous.
    track_event("analysis_started", {
        "role": user_selections.selected_role_display,
        "academic_level": user_selections.selected_level_name,
        "frameworks": sorted(user_selections.all_required_codes)
    })

    # --- STAGE 1: SAFETY CHECK ---
    # This is usually fast, so a simple, static message is fine.
    with st.spinner("⚙️ Performing initial safety check..."):
        if not st.session_state.safety_analysis_result:
            safety_prompt_obj = config_loader.prompts["safety_check_v1"]
            safety_prompt = assemble_safety_prompt(st.session_state.reflection_text, safety_prompt_obj)
            safety_result = call_gemini_for_safety_check(safety_prompt, config_loader)

            # If the API call failed, an error is already displayed. Halt the pipeline.
            if safety_result is None:
                st.session_state.processing = False
                return

            st.session_state.safety_analysis_result = safety_result

    # --- STAGE 2: EVALUATE SAFETY & DECIDE ACTION ---
    can_proceed = False
    if safety_result := st.session_state.safety_analysis_result:
        if not safety_result.is_safe_for_processing:
            track_event("safety_check_distress_detected")
        elif safety_result.pii_detections and not st.session_state.pii_warning_acknowledged:
            flags = sorted([d.flag.value for d in safety_result.pii_detections])
            track_event("safety_check_pii_detected", {"flags": flags})
        else:
            if safety_result.pii_detections and st.session_state.pii_warning_acknowledged:
                flags = sorted([d.flag.value for d in safety_result.pii_detections])
                track_event("pii_warning_acknowledged", {"flags": flags})
            can_proceed = True
    
    # --- STAGE 3: MAIN ANALYSIS (if safe) ---
    if can_proceed:
        # This is the long part, so we use a fun, random message.
        random_message = random.choice(LOADING_MESSAGES)
        spinner_text = f"⚙️ {random_message} (this may take a moment)"
        with st.spinner(spinner_text):
            selected_frameworks_dict = {
                code: user_selections.available_frameworks[code] 
                for code in user_selections.all_required_codes if code in user_selections.available_frameworks
            }
            prompt_obj = config_loader.prompts["portfolio_analysis_v1"]

            # Convert the string key from selections into the expected Enum
            level_key_enum = AcademicLevelKey(user_selections.selected_level_key)

            final_prompt = assemble_analysis_prompt(
                user_selections.role_obj, user_selections.level_obj, level_key_enum,
                st.session_state.reflection_text, selected_frameworks_dict, prompt_obj, 
                user_selections.next_level_name, user_selections.next_level_description, 
                config_loader.llm_config.app.debug_mode, config_loader.academic_levels
            )
            analysis_result = call_gemini_for_analysis(final_prompt, config_loader)

            # If the API call failed, an error is already displayed. Halt the pipeline.
            if analysis_result is None:
                st.session_state.processing = False
                return

            st.session_state.analysis_result = analysis_result

            mapped_competencies = defaultdict(list)
            if analysis_result:
                for c in analysis_result.assessed_competencies:
                    mapped_competencies[c.framework_code].append(c.competency_id)
                for code in mapped_competencies: mapped_competencies[code].sort()

            track_event("analysis_completed", {
                "role": user_selections.selected_role_display, "academic_level": user_selections.selected_level_name,
                "frameworks": sorted(user_selections.all_required_codes), "success": bool(analysis_result),
                "mapped_competency_count": sum(len(ids) for ids in mapped_competencies.values()),
                "mapped_competencies": dict(mapped_competencies)
            })

            if analysis_result:
                st.session_state.last_analysis_reflection = st.session_state.reflection_text
                st.session_state.last_analysis_frameworks = set(user_selections.all_required_codes)
                st.session_state.analysis_just_completed = True
            else:
                st.session_state.last_analysis_reflection, st.session_state.last_analysis_frameworks = None, None
                st.session_state.analysis_just_completed = False

    st.session_state.processing = False
    st.rerun()

def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(
        page_title="Portfolio Mapper AI",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🗺️ AI-Powered Portfolio Mapper")
    st.markdown("Map your clinical reflections against professional competency frameworks using AI. Select your profile from the sidebar to begin.")

    initialize_session_state()
    framework_library, config_loader = load_data()
    if not framework_library or not config_loader:
        return

    selections = render_sidebar(config_loader, framework_library, invalidate_results)

    if selections:
        render_main_inputs(config_loader, selections, clear_state, invalidate_results)
        render_safety_warnings()
        if st.session_state.processing:
            _run_analysis_pipeline(config_loader, selections)
    else:
        st.info("Please select your role from the sidebar to begin.")

    if st.session_state.analysis_result:
        render_results(framework_library)

    render_footer()
