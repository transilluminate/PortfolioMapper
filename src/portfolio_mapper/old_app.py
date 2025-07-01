# src/portfolio_mapper/app.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
Main Streamlit application file for the AI-Powered Portfolio Mapper.
This file is responsible for the user interface and application flow.
"""
from collections import defaultdict
from datetime import datetime
import uuid
import streamlit as st
import pandas as pd

# --- Local Imports ---
from .data_loader import ConfigLoader, FrameworkLoader
from .logic import resolve_allowed_frameworks, assemble_analysis_prompt, assemble_safety_prompt
from .reporting import generate_pdf_report
from .llm_functions import call_gemini_for_analysis, call_gemini_for_safety_check
from .analytics import track_event

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

def _run_analysis_pipeline(
    config_loader,
    role_obj,
    level_obj,
    selected_level_key,
    next_level_name,
    next_level_description,
    available_frameworks,
    all_required_codes,
):
    """
    Encapsulates the entire multi-stage analysis process.
    1. Runs a safety check.
    2. Evaluates the safety result to decide whether to proceed.
    3. Runs the main competency analysis if safe.
    Updates Streamlit session state and triggers a rerun.
    """
    with st.spinner("⏱️ Your reflection is being analysed, this may take a moment..."):
        # --- STAGE 1: SAFETY CHECK (if not already done) ---
        if not st.session_state.safety_analysis_result:
            safety_prompt_obj = config_loader.prompts["safety_check_v1"]
            safety_prompt = assemble_safety_prompt(
                reflection_text=st.session_state.reflection_text,
                prompt_obj=safety_prompt_obj
            )
            safety_result = call_gemini_for_safety_check(safety_prompt, config_loader)
            st.session_state.safety_analysis_result = safety_result

        # --- STAGE 2: EVALUATE SAFETY & DECIDE ACTION ---
        can_proceed = False
        safety_result = st.session_state.safety_analysis_result

        if safety_result:
            if not safety_result.is_safe_for_processing:
                track_event("safety_check_distress_detected")
                pass  # Hard stop for user distress; UI will show error after rerun
            elif safety_result.pii_detections and not st.session_state.pii_warning_acknowledged:
                flags = sorted(list(set([d.flag.value for d in safety_result.pii_detections])))
                track_event("safety_check_pii_detected", {"flags": flags})
                pass  # Soft stop for any PII, awaiting user acknowledgement
            else:
                if safety_result.pii_detections and st.session_state.pii_warning_acknowledged:
                    flags = sorted(list(set([d.flag.value for d in safety_result.pii_detections])))
                    track_event("pii_warning_acknowledged", {"flags": flags})
                # Clean, or user has acknowledged PII warning
                can_proceed = True
        
        # --- STAGE 3: MAIN ANALYSIS (if safe) ---
        if can_proceed:
            selected_frameworks_dict = {
                code: available_frameworks[code] 
                for code in all_required_codes if code in available_frameworks
            }
            prompt_obj = config_loader.prompts["portfolio_analysis_v1"]
            
            final_prompt = assemble_analysis_prompt(
                role_obj, level_obj, selected_level_key, st.session_state.reflection_text, 
                selected_frameworks_dict, prompt_obj, next_level_name, 
                next_level_description, config_loader.llm_config.app.debug_mode,
                config_loader.academic_levels
            )
            
            analysis_result = call_gemini_for_analysis(final_prompt, config_loader)
            st.session_state.analysis_result = analysis_result

            # Prepare mapped competency IDs for tracking, preserving framework association
            mapped_competencies_by_framework = defaultdict(list)
            if analysis_result:
                for c in analysis_result.assessed_competencies:
                    mapped_competencies_by_framework[c.framework_code].append(c.competency_id)
            
            # Sort the lists of competency IDs for consistency
            for framework_code in mapped_competencies_by_framework:
                mapped_competencies_by_framework[framework_code].sort()

            total_mapped_competencies = sum(len(ids) for ids in mapped_competencies_by_framework.values())

            track_event("analysis_completed", {
                "role": role_obj.display_name,
                "academic_level": level_obj.name,
                "frameworks": sorted(all_required_codes),
                "success": bool(analysis_result),
                "mapped_competency_count": total_mapped_competencies,
                "mapped_competencies": dict(mapped_competencies_by_framework)
            })

            if analysis_result:
                st.session_state.last_analysis_reflection = st.session_state.reflection_text
                st.session_state.last_analysis_frameworks = set(all_required_codes)
            else:
                st.session_state.last_analysis_reflection = None
                st.session_state.last_analysis_frameworks = None

        st.session_state.processing = False
        st.rerun()

def main():
    """Main function to run the Streamlit application."""
    
    st.set_page_config(
        page_title="Portfolio Mapper AI",
        page_icon="🗺️",
        initial_sidebar_state="expanded",
        layout="wide"
        )
    
    st.title("🗺️ AI-Powered Portfolio Mapper")

    st.markdown("Map your clinical reflections against professional competency frameworks using AI. Select your profile from the sidebar to begin.")

    # --- Initialize Session State ---
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "reflection_text" not in st.session_state:
        st.session_state.reflection_text = ""
    if "anonymisation_confirmed" not in st.session_state:
        st.session_state.anonymisation_confirmed = False
    if "safety_analysis_result" not in st.session_state:
        st.session_state.safety_analysis_result = None
    if "pii_warning_acknowledged" not in st.session_state:
        st.session_state.pii_warning_acknowledged = False
    if "last_analysis_reflection" not in st.session_state:
        st.session_state.last_analysis_reflection = None
    if "last_analysis_frameworks" not in st.session_state:
        st.session_state.last_analysis_frameworks = None

    def invalidate_results():
        """Callback to clear results when an input changes, forcing re-analysis."""
        st.session_state.analysis_result = None
        st.session_state.safety_analysis_result = None
        st.session_state.pii_warning_acknowledged = False
        st.session_state.last_analysis_reflection = None
        st.session_state.last_analysis_frameworks = None
        # We don't clear 'processing' here as this callback runs on user input.

    def clear_state():
        """Callback to clear reflection text and analysis results."""
        st.session_state.reflection_text = ""
        st.session_state.processing = False # Ensure processing is stopped on clear
        st.session_state.analysis_result = None
        st.session_state.anonymisation_confirmed = False
        st.session_state.last_analysis_reflection = None
        st.session_state.last_analysis_frameworks = None
        st.session_state.safety_analysis_result = None
        st.session_state.pii_warning_acknowledged = False

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
        placeholder="Select your role...",
        on_change=invalidate_results
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
            index=default_level_index,
            on_change=invalidate_results
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
            label_visibility="visible",
            on_change=invalidate_results
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
        
        placeholder_base_text = "Paste your anonymised clinical reflection here.\n\n"
        placeholder_pii_reminder = "Ensure you have removed all Personally Identifiable Information (PII).\n\n"
        placeholder_guidance = f"💡 For a '{level_obj.name}' reflection:\n{level_obj.description}"
        dynamic_placeholder = placeholder_base_text + placeholder_pii_reminder + placeholder_guidance

        st.text_area(
            label="Paste your anonymised clinical reflection here:", # Keep label for accessibility
            label_visibility="collapsed", # But hide it visually
            height=300,
            placeholder=dynamic_placeholder,
            help="Ensure you have removed all Personally Identifiable Information (PII).",
            key="reflection_text",
            on_change=invalidate_results
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

            # 3. Check if there's a pending PII warning that needs acknowledgement
            pii_warning_is_active = False
            if st.session_state.safety_analysis_result:
                if (st.session_state.safety_analysis_result.pii_detections and
                    not st.session_state.analysis_result):
                    pii_warning_is_active = True

            # Set a helpful tooltip message based on the button's disabled state
            # Ensure every component of this check is explicitly a boolean
            button_disabled = bool(
                st.session_state.processing or not is_ready or 
                has_unchanged_result or pii_warning_is_active
            )
            tooltip = None
            if pii_warning_is_active:
                tooltip = "Please review and acknowledge the PII warning below to proceed."
            elif has_unchanged_result:
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
                track_event("analysis_started", {
                    "role": selected_role_display,
                    "academic_level": selected_level_name,
                    "frameworks": sorted(all_required_codes)
                })
                st.session_state.processing = True
                # Reset all results and acknowledgements for a fresh run
                st.session_state.analysis_result = None
                st.session_state.safety_analysis_result = None
                st.session_state.pii_warning_acknowledged = False
                st.rerun()
        
        with col3:
            # Disable the clear button if there's nothing to clear or if processing
            is_clearable = bool(st.session_state.reflection_text.strip()) or bool(st.session_state.analysis_result)
            clear_button_disabled = not is_clearable or st.session_state.processing
            clear_tooltip = "Clear the reflection text and any analysis results."
            if st.session_state.processing:
                clear_tooltip = "Cannot clear while analysis is in progress."
            elif not is_clearable:
                clear_tooltip = "Nothing to clear."
            st.button(
                "🧹 Clear", 
                on_click=clear_state, 
                use_container_width=True,
                disabled=clear_button_disabled,
                help=clear_tooltip
            )

        # --- UI Step 4: Safety & PII Check Results ---

        # This section will display messages from the safety check after it has run
        if (st.session_state.safety_analysis_result and
            not st.session_state.processing and
            not st.session_state.analysis_result):
            safety_result = st.session_state.safety_analysis_result

            # Check 1: User Distress (Hard Stop)
            if not safety_result.is_safe_for_processing:
                st.error("**Analysis Halted: User Distress Detected**", icon="❤️‍🩹")
                st.markdown("""
                    Our safety check suggests this reflection may contain expressions of personal distress or self-harm. As a safety precaution, we cannot process this text further. 
                    
                    #### Support is available
                    If you are in distress, please know that you are not alone and help is available.
                    - **For immediate support:** Contact the Samaritans by calling **116 123** (free, 24/7) or visit [samaritans.org](https://www.samaritans.org/how-we-can-help/contact-samaritan/).
                    - **Professional support:** Consider reaching out to your GP, a trusted colleague, or your organisation's occupational health service.
                """)
            
            # Check 2: PII Detections
            elif safety_result.pii_detections:
                
                with st.form("pii_acknowledgement_form"):

                    st.warning("**Please review your reflection for potential personal information**", icon="⚠️")
                    st.markdown("""
                    Our automated check has highlighted some items that could be personally identifiable. Before proceeding, please review them. 
                    
                    The goal is to ensure your final portfolio entry is properly anonymised. You can either edit your reflection to remove these items or, if you are confident they are not identifiable, proceed with the analysis.
                    """)

                    # Create a more readable list of detected items
                    pii_messages = []
                    for d in safety_result.pii_detections:
                        # Use the AI's explanation for a user-friendly message
                        pii_messages.append(f"- **`{d.text}`**: {d.explanation}")
                    
                    st.markdown("#### Detected Items for Review:")
                    st.markdown("\n".join(pii_messages))

                    submitted = st.form_submit_button(
                        "Acknowledge and Proceed with Analysis",
                        type="primary"
                    )
                    if submitted:
                        st.session_state.pii_warning_acknowledged = True
                        st.session_state.processing = True
                        # Rerun immediately to enter the processing state
                        st.rerun()

        if st.session_state.processing:
            _run_analysis_pipeline(
                config_loader=config_loader,
                role_obj=role_obj,
                level_obj=level_obj,
                selected_level_key=selected_level_key,
                next_level_name=next_level_name,
                next_level_description=next_level_description,
                available_frameworks=available_frameworks,
                all_required_codes=all_required_codes,
            )

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
                    with st.expander(f"**({competency.competency_id}) {competency.competency_text}**"):
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
                "framework_abbreviation",
                "competency_id",
                "achieved_level",
                "justification_for_level",
                "emerging_evidence_for_next_level"
            ]
            df = df[[col for col in column_order if col in df.columns]]
            
            df.rename(columns={
                "framework_abbreviation": "Framework",
                "competency_id": "Competency ID",
                "achieved_level": "Achieved Level",
                "justification_for_level": "Justification",
                "emerging_evidence_for_next_level": "Next Level Evidence"
            }, inplace=True)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "💾 Download as CSV", csv, f"portfolio_analysis_{timestamp}.csv", 
                    "text/csv", use_container_width=True,
                    on_click=track_event, args=("report_downloaded", {"format": "csv"})
                )
            with col2:
                pdf_bytes = generate_pdf_report(
                    analysis_result=analysis_result,
                    available_frameworks=framework_library,
                    reflection_text=st.session_state.reflection_text
                )
                st.download_button(
                    "📄 Download as PDF", pdf_bytes, f"portfolio_analysis_{timestamp}.pdf", 
                    "application/pdf", use_container_width=True,
                    on_click=track_event, args=("report_downloaded", {"format": "pdf"})
                )
        else:
            st.info("No specific competencies were matched based on your reflection.")

    # --- Footer ---
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

if __name__ == '__main__':
    main()
