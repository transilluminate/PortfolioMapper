# src/portfolio_mapper/app.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other commercial use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
Main Streamlit application file for the AI-Powered Portfolio Mapper.
This file is responsible for the user interface and application flow.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd

# --- Local Imports ---
from .data_loader import ConfigLoader, FrameworkLoader
from .logic import resolve_allowed_frameworks, assemble_prompt
from .reporting import generate_pdf_report
from .llm_functions import call_gemini_for_analysis

@st.cache_resource
def load_data():
    """
    Loads all framework and config files and caches them.
    Includes robust error handling for startup failures.
    """
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

def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(page_title="Portfolio Mapper AI", layout="wide")
    st.title("🗺️ AI-Powered Portfolio Mapper")
    st.markdown("This tool uses AI to map your clinical reflections against multiple professional competency frameworks at the same time. No data is stored by this app, however, your reflection text **is** passed to Google Gemini Vertex API for processing. Please see the Google page on [Generative AI and data governance](https://cloud.google.com/vertex-ai/generative-ai/docs/data-governance) for more details.")

    # --- Initialize Session State ---
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "reflection_text" not in st.session_state:
        st.session_state.reflection_text = ""
    if "anonymisation_confirmed" not in st.session_state:
        st.session_state.anonymisation_confirmed = False
    # Track the inputs of the last successful analysis
    if "last_analysis_reflection" not in st.session_state:
        st.session_state.last_analysis_reflection = None
    if "last_analysis_frameworks" not in st.session_state:
        st.session_state.last_analysis_frameworks = None

    def clear_state():
        """Callback to clear reflection text and analysis results."""
        st.session_state.reflection_text = ""
        st.session_state.analysis_result = None
        st.session_state.anonymisation_confirmed = False
        st.session_state.last_analysis_reflection = None
        st.session_state.last_analysis_frameworks = None

    # Load all data at startup and cache it
    framework_library, config_loader = load_data()
    if not framework_library or not config_loader:
        return # Stop execution if data loading failed

    # --- UI Step 1: User Profile ---
    st.sidebar.header("1. Your Profile")
    
    role_keys = list(config_loader.roles.keys())
    role_display_names = [config_loader.roles[key].display_name for key in role_keys]
    
    selected_role_display = st.sidebar.selectbox(
        "Select your Role:",
        options=role_display_names,
        index=None,
        placeholder="Select your role..."
    )

    if selected_role_display:
        # Find the key corresponding to the selected display name
        selected_role_id = role_keys[role_display_names.index(selected_role_display)]
        role_obj = config_loader.roles[selected_role_id]

        level_keys = list(config_loader.academic_levels.keys())
        level_names = [config_loader.academic_levels[key].name for key in level_keys]
        default_level_index = level_keys.index(role_obj.default_academic_level)

        selected_level_name = st.sidebar.selectbox(
            "Academic Level of this Reflection:",
            options=level_names,
            index=default_level_index
        )
        selected_level_key = level_keys[level_names.index(selected_level_name)]
        level_obj = config_loader.academic_levels[selected_level_key]

        # Determine the next academic level for LLM context
        selected_level_index = level_keys.index(selected_level_key)
        next_level_name = "N/A"
        next_level_description = "This is the highest academic level defined."
        if selected_level_index + 1 < len(level_keys):
            next_level_key = level_keys[selected_level_index + 1]
            next_level_obj = config_loader.academic_levels[next_level_key]
            next_level_name = next_level_obj.name
            next_level_description = next_level_obj.description

        # --- UI Step 2: Framework Selection ---
        st.sidebar.header("2. Your Frameworks")

        available_frameworks = resolve_allowed_frameworks(role_obj, framework_library)
        
        if not available_frameworks:
            st.sidebar.warning(f"No frameworks are configured for the '{role_obj.display_name}' role.")
            return

        multiselect_options = {
            f"{fw.metadata.abbreviation}": code
            for code, fw in available_frameworks.items() if fw.metadata.display_in_ui
        }

        selected_display_names = st.sidebar.multiselect(
            "Select one or more frameworks to map against:",
            options=sorted(multiselect_options.keys()),
            default=None,
            label_visibility="visible"
        )
        selected_framework_codes = [multiselect_options[name] for name in selected_display_names]

        # --- Dependency Resolution ---
        all_required_codes = set(selected_framework_codes)
        codes_to_check = list(selected_framework_codes)
        while codes_to_check:
            code = codes_to_check.pop(0)
            framework = framework_library.get(code)
            if framework and framework.metadata.dependencies:
                for dep_code in framework.metadata.dependencies:
                    if dep_code not in all_required_codes:
                        all_required_codes.add(dep_code)
                        codes_to_check.append(dep_code)

        # --- Main Content Area ---
        st.header("3. Your Reflection")
        
        # Reconstruct the multi-line placeholder for better user guidance
        placeholder_base_text = "Paste your anonymised clinical reflection here.\nEnsure you have removed all Personally Identifiable Information (PII).\n\n"
        placeholder_guidance = f"💡 For a '{level_obj.name}' reflection:\n{level_obj.description}"
        dynamic_placeholder = placeholder_base_text + placeholder_guidance

        st.text_area(
            label="Paste your anonymised clinical reflection here:", # Keep label for accessibility
            label_visibility="collapsed", # But hide it visually
            height=300,
            placeholder=dynamic_placeholder,
            help="Ensure you have removed all Personally Identifiable Information (PII).",
            key="reflection_text"
        )

        # --- Action Buttons ---
        col1, col2, col3 = st.columns([3, 3, 1])

        with col1:
            st.checkbox(
                "I confirm my reflection is anonymised.",
                help="You must confirm that all PII has been removed before analysis.",
                key="anonymisation_confirmed"
            )

        with col2:
            # Determine if the button should be enabled
            # 1. Basic readiness check
            min_len = config_loader.llm_config.app.min_reflection_length
            is_ready = bool(
                len(st.session_state.reflection_text.strip()) >= min_len and 
                selected_framework_codes and 
                st.session_state.anonymisation_confirmed
            )

            # 2. Check if the current inputs match the last successful analysis
            has_unchanged_result = False
            if st.session_state.analysis_result:
                reflection_is_same = st.session_state.reflection_text == st.session_state.last_analysis_reflection
                frameworks_are_same = set(all_required_codes) == st.session_state.last_analysis_frameworks
                if reflection_is_same and frameworks_are_same:
                    has_unchanged_result = True

            # Set a helpful tooltip message based on the button's disabled state
            button_disabled = st.session_state.processing or not is_ready or has_unchanged_result
            tooltip = None
            if has_unchanged_result:
                tooltip = "Analysis complete. Change the reflection or frameworks to re-analyse."
            elif st.session_state.processing:
                tooltip = "Analysis is currently in progress..."
            elif not is_ready:
                if len(st.session_state.reflection_text.strip()) < min_len:
                    tooltip = f"Please enter a more detailed reflection (at least {min_len} characters)."
                else:
                    tooltip = "Please select frameworks and confirm anonymisation to enable analysis."

            if st.button(
                "✨ Analyse Reflection",
                type="primary",
                use_container_width=True,
                disabled=button_disabled,
                help=tooltip
            ):
                st.session_state.processing = True
                st.session_state.analysis_result = None # Clear old results
                st.rerun()
        
        with col3:
            # Disable the clear button if there's nothing to clear or if processing
            is_clearable = bool(st.session_state.reflection_text.strip())
            st.button(
                "🧹 Clear", 
                on_click=clear_state, 
                use_container_width=True,
                disabled=not is_clearable or st.session_state.processing
            )

        if st.session_state.processing:
            with st.spinner("⏱️ Your reflection is being analysed... This may take a moment."):
                selected_frameworks_dict = {
                    code: available_frameworks[code] 
                    for code in all_required_codes if code in available_frameworks
                }
                prompt_obj = config_loader.prompts["portfolio_analysis_v1"]
                
                final_prompt = assemble_prompt(
                    role_obj, level_obj, selected_level_key, st.session_state.reflection_text, 
                    selected_frameworks_dict, prompt_obj, next_level_name, 
                    next_level_description, config_loader.llm_config.app.debug_mode,
                    config_loader.academic_levels
                )
                
                analysis_result = call_gemini_for_analysis(final_prompt, config_loader)
                st.session_state.analysis_result = analysis_result

                # If analysis was successful, store the inputs that generated it.
                if analysis_result:
                    st.session_state.last_analysis_reflection = st.session_state.reflection_text
                    st.session_state.last_analysis_frameworks = set(all_required_codes)
                else: # If analysis failed, clear the state to allow a retry.
                    st.session_state.last_analysis_reflection = None
                    st.session_state.last_analysis_frameworks = None

                st.session_state.processing = False
                st.rerun()
    else:
        # If no role is selected, show disabled fields and a prompt.
        st.sidebar.selectbox("Academic Level of this Reflection:", options=[], disabled=True)
        st.sidebar.multiselect("Choose frameworks to map against:", options=[], disabled=True)
        st.info("Please select your role from the sidebar to begin.")

    if st.session_state.analysis_result:
        analysis_result = st.session_state.analysis_result
        st.success("✅ Analysis Complete!")
        st.header("🔑 Overall Summary")
        st.markdown(analysis_result.overall_summary)

        st.header("💡 Suggested Matching Competencies")
        if analysis_result.assessed_competencies:
            # Group competencies by framework for a cleaner display
            grouped_competencies = defaultdict(list)
            for competency in analysis_result.assessed_competencies:
                grouped_competencies[competency.framework_code].append(competency)

            # Display results, grouped by framework using the full framework_library for lookups
            for framework_code, competencies in grouped_competencies.items():
                framework_obj = framework_library.get(framework_code)
                
                if framework_obj:
                    st.subheader(f"{framework_obj.metadata.abbreviation}: {framework_obj.metadata.title}")
                else:
                    st.subheader(f"Matches for: {framework_code}")
                
                for competency in sorted(competencies, key=lambda c: c.competency_id):
                    with st.expander(f"**{competency.competency_id}: {competency.competency_text}**"):
                        st.markdown(f"**Achieved Level:** `{competency.achieved_level}`")
                        st.info(f"**Justification:** {competency.justification_for_level}")
                        if competency.emerging_evidence_for_next_level:
                            st.warning(f"**Emerging Evidence for Next Level:** {competency.emerging_evidence_for_next_level}")
            
            st.subheader("📋 Tabular View & Download")
            
            competencies_data = [c.model_dump() for c in analysis_result.assessed_competencies]
            df = pd.DataFrame(competencies_data)
            
            # Add framework abbreviation for user-friendliness
            df['framework_abbreviation'] = df['framework_code'].apply(
                lambda code: framework_library.get(code).metadata.abbreviation if framework_library.get(code) else code
            )
            
            column_order = [
                "framework_abbreviation", "competency_id", "achieved_level",
                "justification_for_level", "emerging_evidence_for_next_level"
            ]
            df = df[[col for col in column_order if col in df.columns]]
            
            df.rename(columns={
                "framework_abbreviation": "Framework", "competency_id": "Competency ID",
                "achieved_level": "Achieved Level", "justification_for_level": "Justification",
                "emerging_evidence_for_next_level": "Next Level Evidence"
            }, inplace=True)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("💾 Download as CSV", csv, f"portfolio_analysis_{timestamp}.csv", "text/csv", use_container_width=True)
            with col2:
                pdf_bytes = generate_pdf_report(analysis_result, framework_library)
                st.download_button("📄 Download as PDF", pdf_bytes, f"portfolio_analysis_{timestamp}.pdf", "application/pdf", use_container_width=True)
        else:
            st.info("No specific competencies were matched based on your reflection.")

if __name__ == '__main__':
    main()
