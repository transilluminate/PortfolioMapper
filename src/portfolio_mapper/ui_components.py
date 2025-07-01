# src/portfolio_mapper/ui_components.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
This module contains all UI rendering functions for the Streamlit app,
separating the view logic from the main application flow.
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional

import streamlit as st
import pandas as pd

from .analytics import track_event

from .data_loader import ConfigLoader
from .logic import resolve_allowed_frameworks
from .models.framework import FrameworkFile
from .models.ui import UserSelections
from .reporting import generate_pdf_report

def render_sidebar(config_loader: ConfigLoader, framework_library: Dict[str, FrameworkFile], invalidate_callback) -> Optional[UserSelections]:
    """Renders the sidebar UI and returns a UserSelections object if complete."""
    st.sidebar.header("1. Your Profile")
    
    role_keys = list(config_loader.roles.keys())
    role_display_names = [config_loader.roles[key].display_name for key in role_keys]
    
    selected_role_display = st.sidebar.selectbox(
        "Select your Role:", options=role_display_names, index=None,
        placeholder="Select your role...", on_change=invalidate_callback
    )

    if not selected_role_display:
        st.sidebar.selectbox("Academic Level of this Reflection:", options=[], disabled=True)
        st.sidebar.multiselect("Choose frameworks to map against:", options=[], disabled=True)
        return None

    selected_role_id = role_keys[role_display_names.index(selected_role_display)]
    role_obj = config_loader.roles[selected_role_id]

    level_keys = list(config_loader.academic_levels.keys())
    level_names = [config_loader.academic_levels[key].name for key in level_keys]
    default_level_index = level_keys.index(role_obj.default_academic_level)

    selected_level_name = st.sidebar.selectbox(
        "Academic Level of this Reflection:", options=level_names,
        index=default_level_index, on_change=invalidate_callback
    )
    selected_level_key = level_keys[level_names.index(selected_level_name)]
    level_obj = config_loader.academic_levels[selected_level_key]

    selected_level_index = level_keys.index(selected_level_key)
    next_level_name, next_level_description = "N/A", "This is the highest academic level defined."
    if selected_level_index + 1 < len(level_keys):
        next_level_key = level_keys[selected_level_index + 1]
        next_level_obj = config_loader.academic_levels[next_level_key]
        next_level_name, next_level_description = next_level_obj.name, next_level_obj.description

    st.sidebar.header("2. Your Frameworks")
    available_frameworks = resolve_allowed_frameworks(role_obj, framework_library)
    
    if not available_frameworks:
        st.sidebar.warning(f"No frameworks are configured for the '{role_obj.display_name}' role.")
        return None

    multiselect_options = {fw.metadata.abbreviation: code for code, fw in available_frameworks.items() if fw.metadata.display_in_ui}
    selected_display_names = st.sidebar.multiselect(
        "Select one or more frameworks:", options=sorted(multiselect_options.keys()),
        default=None, on_change=invalidate_callback
    )
    selected_framework_codes = [multiselect_options[name] for name in selected_display_names]

    all_required_codes = set(selected_framework_codes)
    codes_to_check = list(selected_framework_codes)
    while codes_to_check:
        code = codes_to_check.pop(0)
        if framework := framework_library.get(code):
            if framework.metadata.dependencies:
                for dep_code in framework.metadata.dependencies:
                    if dep_code not in all_required_codes:
                        all_required_codes.add(dep_code)
                        codes_to_check.append(dep_code)

    return UserSelections(
        role_obj=role_obj, level_obj=level_obj, selected_level_key=selected_level_key,
        next_level_name=next_level_name, next_level_description=next_level_description,
        available_frameworks=available_frameworks, selected_framework_codes=selected_framework_codes,
        all_required_codes=all_required_codes, selected_role_display=selected_role_display,
        selected_level_name=selected_level_name
    )

def render_main_inputs(config_loader: ConfigLoader, user_selections: UserSelections, clear_state_callback, invalidate_callback):
    """Renders the main page content area for user input."""
    st.header("3. Your Reflection")
    
    placeholder_guidance = f"💡 For a '{user_selections.level_obj.name}' reflection:\n{user_selections.level_obj.description}"
    dynamic_placeholder = "Paste your anonymised clinical reflection here.\n\n" + placeholder_guidance

    st.text_area(
        label="Paste your anonymised clinical reflection here:", label_visibility="collapsed",
        height=300, placeholder=dynamic_placeholder, key="reflection_text",
        on_change=invalidate_callback
    )

    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        st.checkbox(
            "I confirm my reflection is anonymised.",
            help="You must confirm that all PII has been removed before analysis.",
            key="anonymisation_confirmed"
        )

    with col2:
        # Determine if the button should be enabled
        min_len = config_loader.llm_config.app.min_reflection_length
        is_ready = bool(
            len(st.session_state.reflection_text.strip()) >= min_len and 
            user_selections.selected_framework_codes and 
            st.session_state.anonymisation_confirmed
        )

        has_unchanged_result = False
        if st.session_state.analysis_result and st.session_state.last_analysis_reflection is not None:
            reflection_is_same = st.session_state.reflection_text == st.session_state.last_analysis_reflection
            frameworks_are_same = set(user_selections.all_required_codes) == st.session_state.last_analysis_frameworks
            if reflection_is_same and frameworks_are_same:
                has_unchanged_result = True

        # 3. Check for safety flags that should disable the button
        pii_warning_is_active = False
        user_distress_is_active = False
        if st.session_state.safety_analysis_result:
            if not st.session_state.safety_analysis_result.is_safe_for_processing:
                user_distress_is_active = True
            elif (st.session_state.safety_analysis_result.pii_detections and not st.session_state.analysis_result):
                pii_warning_is_active = True

        button_disabled = bool(st.session_state.processing or not is_ready or has_unchanged_result or pii_warning_is_active or user_distress_is_active)
        tooltip = "Please select frameworks and confirm anonymisation to enable analysis."
        if user_distress_is_active:
            tooltip = "Analysis is disabled due to a user safety concern. Please see the message below."
        elif pii_warning_is_active:
            tooltip = "Please review and acknowledge the PII warning below to proceed."
        elif has_unchanged_result: tooltip = "Analysis complete. Change inputs to re-analyse."
        elif st.session_state.processing: tooltip = "Analysis is in progress..."
        elif len(st.session_state.reflection_text.strip()) < min_len: tooltip = f"Please enter at least {min_len} characters."

        if st.button("✨ Analyse Reflection", type="primary", use_container_width=True, disabled=button_disabled, help=tooltip):
            st.session_state.processing = True
            # Explicitly clear previous results to ensure a clean run
            st.session_state.analysis_result = None
            st.session_state.safety_analysis_result = None
            st.session_state.pii_warning_acknowledged = False
            st.rerun()
    
    with col3:
        is_clearable = bool(st.session_state.reflection_text.strip()) or bool(st.session_state.analysis_result)
        clear_button_disabled = not is_clearable or st.session_state.processing
        clear_tooltip = "Clear the reflection text and any analysis results."
        if st.session_state.processing: clear_tooltip = "Cannot clear while analysis is in progress."
        elif not is_clearable: clear_tooltip = "Nothing to clear."
        st.button("🧹 Clear", on_click=clear_state_callback, use_container_width=True, disabled=clear_button_disabled, help=clear_tooltip)

def render_safety_warnings():
    """Renders the user distress or PII warning section if applicable."""
    if (st.session_state.safety_analysis_result and
        not st.session_state.processing and
        not st.session_state.analysis_result):
        safety_result = st.session_state.safety_analysis_result

        if not safety_result.is_safe_for_processing:
            st.error("**Analysis Halted: User Distress Detected**", icon="❤️‍🩹")
            st.markdown("""
                Our safety check suggests this reflection may contain expressions of personal distress or self-harm. As a safety precaution, we cannot process this text further. 
                
                #### Support is available
                If you are in distress, please know that you are not alone and help is available.
                - **For immediate support:** Contact the Samaritans by calling **116 123** (free, 24/7) or visit [samaritans.org](https://www.samaritans.org/how-we-can-help/contact-samaritan/).
                - **Professional support:** Consider reaching out to your GP, a trusted colleague, or your organisation's occupational health service.
            """)
        elif safety_result.pii_detections:
            with st.form("pii_acknowledgement_form"):
                st.warning("**Please review your reflection for potential personal information**", icon="⚠️")
                st.markdown("""
                Our automated check has highlighted some items that could be personally identifiable. Before proceeding, please review them. You can either edit your reflection to remove these items or, if you are confident they are not identifiable, proceed with the analysis.
                """)
                pii_messages = [f"- **`{d.text}`**: {d.explanation}" for d in safety_result.pii_detections]
                st.markdown("#### Detected Items for Review:\n" + "\n".join(pii_messages))
                if st.form_submit_button("Acknowledge and Proceed with Analysis", type="primary"):
                    st.session_state.pii_warning_acknowledged = True
                    st.session_state.processing = True
                    st.rerun()

def render_results(framework_library: Dict[str, FrameworkFile]):
    """Renders the final analysis results section."""
    analysis_result = st.session_state.analysis_result
    st.success("✅ Analysis Complete!")
    st.header("🔑 Overall Summary")
    st.markdown(analysis_result.overall_summary)

    st.header("💡 Suggested Matching Competencies")
    if analysis_result.assessed_competencies:
        # Sort competencies by strength as a fallback, though the prompt asks the LLM to do this.
        sorted_competencies = sorted(
            analysis_result.assessed_competencies, 
            key=lambda c: c.match_strength, 
            reverse=True
        )
        grouped_competencies = defaultdict(list)
        for competency in sorted_competencies:
            grouped_competencies[competency.framework_code].append(competency)

        for framework_code, competencies in grouped_competencies.items():
            framework_obj = framework_library.get(framework_code)
            st.subheader(f"{framework_obj.metadata.abbreviation}: {framework_obj.metadata.title}" if framework_obj else f"Matches for: {framework_code}")
            for competency in competencies: # Already sorted by strength
                with st.expander(f"**({competency.competency_id}) {competency.competency_text}**"):
                    st.markdown(f"**Match Strength:** {'⭐' * competency.match_strength} ({competency.match_strength}/5)  \n**Achieved Level:** `{competency.achieved_level}`")
                    st.info(f"**Justification:** {competency.justification_for_level}")
                    if competency.emerging_evidence_for_next_level:
                        st.warning(f"**Emerging Evidence for Next Level:** {competency.emerging_evidence_for_next_level}")
        
        st.subheader("📋 Tabular View & Download")
        df = pd.DataFrame([c.model_dump() for c in analysis_result.assessed_competencies])
        df['framework_abbreviation'] = df['framework_code'].apply(lambda code: framework_library.get(code).metadata.abbreviation if framework_library.get(code) else code)
        column_order = ["framework_abbreviation", "competency_id", "achieved_level", "justification_for_level", "emerging_evidence_for_next_level"]
        df = df[[col for col in column_order if col in df.columns]]
        df.rename(columns={"framework_abbreviation": "Framework", "competency_id": "Competency ID", "achieved_level": "Achieved Level", "justification_for_level": "Justification", "emerging_evidence_for_next_level": "Next Level Evidence"}, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("💾 Download as CSV", csv, f"portfolio_analysis_{timestamp}.csv", "text/csv", use_container_width=True, on_click=track_event, args=("report_downloaded", {"format": "csv"}))
        with col2:
            pdf_bytes = generate_pdf_report(analysis_result=analysis_result, available_frameworks=framework_library, reflection_text=st.session_state.reflection_text)
            st.download_button("📄 Download as PDF", pdf_bytes, f"portfolio_analysis_{timestamp}.pdf", "application/pdf", use_container_width=True, on_click=track_event, args=("report_downloaded", {"format": "pdf"}))
    else:
        st.info("No specific competencies were matched based on your reflection.")

def render_footer():
    """Renders the expandable footer with app information."""
    with st.expander("About this App & Data Handling"):
        st.markdown(
            """
            #### :material/psychology: How does this work?
            This tool acts as an intelligent assistant to help you understand your own practice. When you submit a reflection, the app doesn't just do a simple keyword search. Instead, it performs a sophisticated, multi-step process:

            1.  **Packaging the Prompt:** It takes your reflection, the competency frameworks you selected, and a detailed set of instructions, and bundles them into a single, comprehensive "prompt".
            2.  **AI Analysis:** This entire package is sent to Google's Gemini AI model. The AI is instructed to act like an expert clinical supervisor. Its job is to meticulously read your reflection and find direct evidence that maps to the specific competencies in the frameworks.
            3.  **Structured Feedback:** The AI then provides structured feedback, justifying every match it finds by quoting your own words and explaining how it aligns with the competency's requirements.

            This systematic approach provides a consistent and objective first pass of your reflection, saving you hours of manually cross-referencing documents.

            #### :material/school: What are the 'Academic Levels'?
            A key feature of this tool is its ability to assess not just *what* you did, but *how well you reflected on it*. The academic levels provide a structured way to evaluate the depth of your critical thinking.

            They are inspired by established educational models like **Miller's Pyramid of Clinical Competence** (*Knows -> Knows How -> Shows How -> Does*) and extend into higher levels of academic and systemic thinking. The levels are:

            -   **Foundational:** *What happened?* (Describing the event)
            -   **Developing:** *How did I apply my knowledge?* (Connecting theory to practice)
            -   **Graduate:** *Did my application of knowledge work?* (Evaluating outcomes)
            -   **Advanced:** *How did I handle complexity and uncertainty?* (Analysing nuance)
            -   **Masters Level:** *How does my practice compare to the evidence base?* (Critiquing and synthesising)
            -   **Doctoral Level:** *What new idea or insight does this generate?* (Challenging paradigms)

            By assessing against this scale, the AI can provide targeted feedback to help you deepen your reflective practice and progress to the next level.

            #### :material/warning: Data Handling
            - **Do not submit sensitive, confidential, or personal information to this App.**
            - The app collects **anonymous usage data** only (e.g., which roles and frameworks are used).
            - No reflections are stored by this app.
            - Your reflections **are** passed to the Google Gemini API for processing:
                - This is using the free-tier, and as such Google "...*uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies, including Google's enterprise features, products, and services*...".
                - Read [How Google Uses Your Data](https://ai.google.dev/gemini-api/terms#data-use-unpaid) for more information.

            #### :material/copyright: Copyright and License
            - Copyright (c) Adrian Robinson 2025.
            - The source code for this app is available on [GitHub](https://github.com/transilluminate/PortfolioMapper).
            - This software is dual-licensed: MIT License (for NHS use only) and a Commercial License (for other use).
            """
        )