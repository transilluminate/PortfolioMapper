# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other commercial use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

import streamlit as st
import google.generativeai as genai
import json
from typing import Dict, Any
from mapping_models import MappingResult
from pydantic import ValidationError

GEMINI_MODEL_NAME = "gemini-2.0-flash"

@st.cache_resource
def get_llm_client() -> genai.GenerativeModel | None:
    """
    Initializes the Google Gemini client.
    Uses Streamlit's resource cache to initialize the client only once per session.
    Any errors during initialization will be clearly displayed in the app.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("`GOOGLE_API_KEY` not found in Streamlit secrets. Please add it to `.streamlit/secrets.toml`.")
        return None

    try:
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model_name=GEMINI_MODEL_NAME)
        return client
    except Exception as e:
        st.error("An error occurred while initializing the Google Gemini client. This could be due to an invalid API key or missing permissions in your Google Cloud project.")
        st.exception(e)
        return None

def _create_system_prompt(schemas: Dict[str, Any]) -> str:
    """Builds the detailed system prompt for the LLM."""
    schemas_str = json.dumps(schemas, indent=2)
    return f"""\
You are an expert in clinical competency frameworks and portfolio mapping. Your task is to analyze a user-provided clinical reflection and map it against the provided JSON competency frameworks.

**Instructions:**
1.  **Analyze the Reflection:** Carefully read the user's reflection.
2.  **Map to Competencies:** For each provided framework, identify specific capabilities that are demonstrated in the reflection.
3.  **Create `CompetencyMatch` objects:** For each match, you must:
    -   Provide the `framework_short_title` from the schema's metadata.
    -   Construct the full `competency_id` in the format '[SHORT_TITLE:SECTION_TITLE:ID]'.
    -   Write a `justification` that **quotes the relevant part of the reflection** and explains the link.
    -   Assign a `strength_of_match` from 1 (weak) to 5 (strong).
    -   If the strength is 3 or less, provide a constructive `improvement_suggestion`.
4.  **Identify `PotentialCompetency`:** Identify up to 5 key competencies that are **not** met but are closely related to the reflection. For each, provide a `suggestion` on how the user could expand their reflection to meet it. This is for growth.
    -   For each `PotentialCompetency`, you must also provide the `framework_short_title`.
5.  **Write a Summary:** Provide a brief, high-level `summary` of the mapping.
6.  **Output:** You must return a valid JSON object that conforms to the `MappingResult` Pydantic schema.
    -   Ensure the top-level keys for the output JSON are `summary`, `matches`, and `potential_matches` (all in snake_case).

**Competency Frameworks:**
```json
{schemas_str}
```

**JSON Output Example:**
```json
{{
  "summary": "This is a high-level summary of the reflection's mapping.",
  "matches": [
    {{
      "framework_short_title": "CfAP Advanced Practice",
      "competency_id": "CfAP Advanced Practice:Clinical Practice:1.1",
      "justification": "The reflection states 'I always work within my scope of practice', which directly demonstrates this competency.",
      "strength_of_match": 5,
      "improvement_suggestion": null
    }},
    {{
      "framework_short_title": "RPS Prescribing Competencies",
      "competency_id": "RPS Prescribing Competencies:The Consultation: Prescribe:4.1",
      "justification": "The reflection mentions 'I prescribed amoxicillin', linking to the ability to prescribe with awareness of actions.",
      "strength_of_match": 4,
      "improvement_suggestion": "Could elaborate on the specific considerations for amoxicillin in this patient."
    }}
  ],
  "potential_matches": [
    {{
      "framework_short_title": "HCPC Paramedic Standards",
      "competency_id": "HCPC Paramedic Standards:Practise as an autonomous professional, exercising their own professional judgement:4.9",
      "suggestion": "The reflection could be expanded to describe how you managed an unpredictable situation independently, demonstrating autonomous judgment."
    }},
    {{
      "framework_short_title": "CfAP Advanced Practice",
      "competency_id": "CfAP Advanced Practice:Research:4.5",
      "suggestion": "Consider adding how this experience might lead to identifying a need for further research in your area of practice."
    }}
  ]
}}
```"""

def _clean_json_response(raw_text: str) -> str:
    """
    Cleans the raw text response from the LLM to extract the JSON block.
    LLMs often wrap JSON in ```json ... ``` which needs to be removed.
    """
    # Find the start of the JSON block
    start_index = raw_text.find('{')
    # Find the end of the JSON block
    end_index = raw_text.rfind('}')
    
    if start_index == -1 or end_index == -1:
        return "" # Return empty string if no JSON object is found
        
    return raw_text[start_index : end_index + 1]

def get_mapping_from_llm(reflection: str, schemas: Dict[str, Any]) -> MappingResult | None:
    """
    Calls the LLM, gets a raw text response, and parses it into a Pydantic model.
    """
    client = get_llm_client()
    if not client:
        return None

    full_prompt = f"""{_create_system_prompt(schemas)}

Here is my clinical reflection:
---
{reflection}"""
    
    raw_text = ""
    mapping_data = {}
    try:
        response = client.generate_content(full_prompt)
        raw_text = response.text
        
        cleaned_json_str = _clean_json_response(raw_text)
        if not cleaned_json_str:
            st.error("The AI did not return a valid JSON object in its response.")
            st.code(raw_text, language="text")
            return None
            
        mapping_data = json.loads(cleaned_json_str)

        # The AI sometimes nests the result in a 'mapping' key.
        data_to_validate = mapping_data.get('mapping', mapping_data)

        return MappingResult.model_validate(data_to_validate)
    except json.JSONDecodeError:
        st.error("Failed to parse the AI's response as JSON.")
        st.code(raw_text, language='text')
        return None
    except ValidationError as e:
        st.error("The AI's JSON response did not match the required format.")
        st.write("The AI returned the following data structure, which could not be validated:")
        st.json(mapping_data)
        st.write("Pydantic validation errors:")
        st.exception(e)
        return None
    except Exception as e:
        st.error("An unexpected error occurred during the mapping process.")
        st.exception(e)
        return None
