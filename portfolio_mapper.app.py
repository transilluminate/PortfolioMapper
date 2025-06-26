# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other commercial use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

import streamlit as st
import pandas as pd
import json
from llm_functions import get_mapping_from_llm

# --- Page Configuration ---
st.set_page_config(
    page_title="Portfolio Mapper",
    page_icon="🗺️",
    layout="wide",
)

# --- State Management ---
if 'mapping_result' not in st.session_state:
    st.session_state.mapping_result = None
if 'processing' not in st.session_state:
    # Tracks if the AI is currently processing
    st.session_state.processing = False 
if 'last_status_message' not in st.session_state:
    st.session_state.last_status_message = None

@st.cache_data
def _combine_hcpc_schemas(profession_schema: dict, generic_schema: dict) -> dict:
    """
    Combines a profession-specific HCPC schema with the generic HCPC schema.
    Capabilities from both are merged under the profession-specific title.
    """
    combined_schema = profession_schema.copy()

    # Update metadata to reflect combination
    combined_schema['metadata']['title'] = (
        f"{profession_schema['metadata']['title']} (including Generic Capabilities)"
    )

    # Create a dictionary for easier merging of sections
    combined_sections_map = {
        section['title']: section['capabilities']
        for section in generic_schema.get('sections', [])
    }

    # Merge profession-specific capabilities.
    # If a section title exists, append capabilities.
    # Otherwise, add the new section.
    for prof_section in profession_schema.get('sections', []):
        title = prof_section['title']
        if title in combined_sections_map:
            # Append profession-specific capabilities to generic ones
            combined_sections_map[title].extend(prof_section['capabilities'])
        else:
            # Add new profession-specific section
            combined_sections_map[title] = prof_section['capabilities']

    # Convert the map back to a list of sections
    combined_schema['sections'] = [
        {'title': title, 'capabilities': capabilities}
        for title, capabilities in combined_sections_map.items()
    ]
    return combined_schema

@st.cache_data
def load_schemas(selected_framework_names: list[str], schema_map: dict) -> dict:
    """Loads the content of selected schema files."""
    schemas = {}
    for name in selected_framework_names:
        file_path_str = schema_map.get(name)
        if file_path_str:
            try:
                with open(file_path_str) as f:
                    current_schema_content = json.load(f)

                # Special handling for HCPC profession-specific schemas
                if name.startswith("HCPC") and name != "HCPC Generic":
                    generic_file_path = schema_map.get("HCPC Generic")
                    if generic_file_path:
                        with open(generic_file_path) as f_generic:
                            generic_schema_content = json.load(f_generic)
                        
                        combined_hcpc_schema = _combine_hcpc_schemas(current_schema_content, generic_schema_content)
                        short_title = combined_hcpc_schema.get("metadata", {}).get("short title", name)
                        schemas[short_title] = combined_hcpc_schema
                    else:
                        st.warning(f"HCPC Generic schema not found at {generic_file_path}. Only profession-specific capabilities will be loaded for {name}.")
                        # Load only the specific one if generic is missing
                        schemas[name] = current_schema_content 
                else:
                    short_title = current_schema_content.get("metadata", {}).get("short title", name)
                    schemas[short_title] = current_schema_content
            except FileNotFoundError:
                st.error(f"Schema file not found: {file_path_str}")
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON from file: {file_path_str}")
    return schemas

def reset_app():
    """Resets the session state to start over."""
    st.session_state.mapping_result = None
    st.session_state.processing = False
    st.session_state.last_status_message = None

# --- Main App ---
st.title("🗺️ AI Portfolio Mapper")
st.markdown("This tool uses AI to map your clinical reflections against multiple professional competency frameworks at the same time. Your data is not stored.")

# --- Input Section ---
col1, col2 = st.columns([2, 1]) # Give more space to the text area

with col1:
    st.subheader("Your Reflection")
    reflection_text = st.text_area(
        "Paste your anonymised clinical reflection here.",
        placeholder="Paste your anonymised clinical reflection here.\n\nEnsure you have removed all Personally Identifiable Information (PII) like names, specific locations, or exact dates.\n\nTop tip: use a reflective model, such as Borton's (1970) 'What? So What? What Now?' model.",
        height=400,
        key="reflection_text",
        help="Ensure you have removed all Personally Identifiable Information (PII) like names, specific locations, or exact dates.",
        label_visibility="collapsed"
    )

    # Checkbox for anonymisation confirmation
    anonymisation_confirmed = st.checkbox(
        "I confirm my reflection is anonymised.",
        key="anonymisation_confirmed"
    )

with col2:
    # Define schema files here, as it's used by the checkboxes
    schema_files = {
        "CfAP Advanced Practice Capabilities": "Schemas/cfap_ap.json",
        "RPS Prescribing Competencies": "Schemas/rps_prescribing.json",        
        "NMC Nursing Standards": "Schemas/nmc_nursing.json",
        "HCPC Generic": "Schemas/hcpc_generic.json", # Internal use
        "HCPC Occupational Therapy Standards": "Schemas/hcpc_ot.json",
        "HCPC Paramedic Standards": "Schemas/hcpc_pa.json",
        "HCPC Physiotherapy Standards": "Schemas/hcpc_ph.json", 
    }
    framework_options = [key for key in schema_files.keys() if key != "HCPC Generic"]

    # Framework selection
    st.subheader("Select Frameworks")
    selected_frameworks = []
    st.write("Choose the competency frameworks to map against:")
    for option in framework_options:
        if st.checkbox(option, key=f"framework_checkbox_{option}"):
            selected_frameworks.append(option)

# Map Reflection Button
submit_button = st.button(
    "Map Reflection",
    type="primary",
    use_container_width=True,
    disabled=not all([reflection_text, selected_frameworks, anonymisation_confirmed]) or st.session_state.processing
)

# Display persistent status message
if st.session_state.last_status_message:
    # Check for 'complete' in message
    if "complete" in st.session_state.last_status_message.lower():
        st.success(st.session_state.last_status_message)
    else: # Assume it's an error or other message
        st.error(st.session_state.last_status_message)

# --- Processing Logic ---
if submit_button and not st.session_state.processing:
    # Only run if button clicked and not already processing
    st.session_state.processing = True
    st.session_state.mapping_result = None # Clear previous results
    st.session_state.last_status_message = None # Clear previous status message
    try:
        # Use a placeholder for the status message to keep it persistent
        status_placeholder = st.empty()
        with status_placeholder.status("Starting mapping process...", expanded=True) as status:
            status.update(label="Loading selected competency frameworks...", state="running")
            loaded_schemas = load_schemas(selected_frameworks, schema_files)
            if not loaded_schemas:
                status.update(label="Error loading schemas", state="error")
                st.error("Could not load the selected schema files. Please check they exist and are correctly formatted.")
                st.session_state.last_status_message = "Error loading schemas. Please check console for details."
            else:
                status.update(label="Asking AI to map reflection... (this may take a moment)", state="running")
                mapping_result = get_mapping_from_llm(reflection_text, loaded_schemas)
                if mapping_result:
                    st.session_state.mapping_result = mapping_result
                    st.session_state.last_status_message = "Mapping complete! Scroll down for results."
                    status.update(label=st.session_state.last_status_message, state="complete") # Update status for immediate display
                else:
                    status.update(label="Mapping Failed", state="error")
                    st.session_state.last_status_message = "Mapping Failed. Please check console for details."
    finally:
        st.session_state.processing = False
        st.rerun() # Rerun to update UI with results and re-enable button

# Results
if st.session_state.mapping_result:
    result = st.session_state.mapping_result
    st.header("Mapping Summary")
    st.markdown(result.summary)

    st.header("✅ Competency Matches")
    st.markdown("Double click the cells to expand and edit the text.")
    if result.matches:
        df_matches = pd.DataFrame([match.model_dump() for match in result.matches]) # Convert Pydantic models to DataFrame
        edited_df = st.data_editor(
            df_matches,
            column_config={
                "framework_short_title": "Framework",
                "competency_id": "Competency ID",
                "strength_of_match": "Strength",
                "justification": st.column_config.TextColumn(
                    "Justification",
                    width="large",                ),
                "improvement_suggestion": st.column_config.TextColumn(
                    "Improvement Suggestion",
                    width="large",
                )
            },
            use_container_width=True,
            num_rows="dynamic",
            key="editor_matches"
        )
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Mapping as CSV", data=csv, file_name="competency_mapping.csv", mime="text/csv")
    else:
        st.info("No direct competency matches were found.")

    st.header("💡 Key Areas for Growth")
    st.markdown("Double click the cells to expand and edit the text.")
    if result.potential_matches:
        df_potential = pd.DataFrame([match.model_dump() for match in result.potential_matches])
        st.dataframe(
            df_potential,
            column_config={
                "framework_short_title": "Framework",
                "competency_id": "Competency ID",
                "suggestion": st.column_config.TextColumn(
                    "Suggestion for Reflection",
                    width="large",
                )
            },
            use_container_width=True,
            hide_index=True
        )
        csv_potential = df_potential.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Key Areas for Growth as CSV", data=csv_potential, file_name="potential_growth.csv", mime="text/csv")
    else:
        st.info("No specific growth opportunities were identified.")
