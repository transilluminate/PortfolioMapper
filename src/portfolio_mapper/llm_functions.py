# src/portfolio_mapper/llm_functions.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

import streamlit as st
import google.generativeai as genai
from typing import Optional, TYPE_CHECKING
from .models.llm_response import LLMAnalysisResult
from .models.safety import SafetyAnalysis
from pydantic import ValidationError

# Use a forward reference for the type hint to avoid a circular import
if TYPE_CHECKING:
    from .data_loader import ConfigLoader

@st.cache_resource
def get_llm_client(_config_loader: "ConfigLoader") -> Optional[genai.GenerativeModel]:
    """
    Initializes and caches the Google Gemini client using settings from the
    provided ConfigLoader. The argument is prefixed with an underscore to
    indicate it's primarily used for caching purposes.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("`GOOGLE_API_KEY` not found. Please add it to `.streamlit/secrets.toml`.")
        return None
    try:
        genai.configure(api_key=api_key)
        
        # Get config from the loader
        gemini_config = _config_loader.llm_config.gemini
        
        # Convert Pydantic models to dictionaries for the SDK
        safety_settings_dict = [s.model_dump() for s in gemini_config.safety_settings]

        return genai.GenerativeModel(
            model_name=gemini_config.model_name, 
            safety_settings=safety_settings_dict
        )
    except Exception as e:
        st.error("Failed to initialize the Google Gemini client.")
        st.exception(e)
        return None

def call_gemini_for_safety_check(prompt: str, config_loader: "ConfigLoader") -> Optional[SafetyAnalysis]:
    """Calls the Gemini API for a safety check, requesting a JSON response, and parses it."""
    client = get_llm_client(config_loader)
    if not client:
        return None

    # Prepare the generation config from our loaded settings
    gemini_config = config_loader.llm_config.gemini
    gen_config_dict = gemini_config.generation_config.model_dump(exclude_none=True)
    
    # Ensure JSON mode is always enabled
    gen_config_dict["response_mime_type"] = "application/json"
    
    generation_config = genai.types.GenerationConfig(**gen_config_dict)

    print("--- Calling Gemini API for Safety Check (REAL) ---")
    try:
        # Pass both the prompt and the generation config to the client
        response = client.generate_content(prompt, generation_config=generation_config)
        
        if config_loader.llm_config.app.debug_mode:
            # --- DEBUGGING: Dump raw JSON response to console ---
            print("\n--- LLM SAFETY OUTPUT: RAW JSON RESPONSE ---")
            print(response.text)
            print("-------------------------------------\n")

        return SafetyAnalysis.model_validate_json(response.text)
    except ValidationError as e:
        st.error("The AI's safety check response did not match the required format.")
        st.exception(e)
        st.write("Raw AI Response:")
        st.code(response.text if 'response' in locals() else "No response from AI.", language="json")
        return None
    except Exception as e:
        st.error("An unexpected error occurred while communicating with the Gemini API for the safety check.")
        st.exception(e)
        return None

def call_gemini_for_analysis(prompt: str, config_loader: "ConfigLoader") -> Optional[LLMAnalysisResult]:
    """Calls the Gemini API, requesting a JSON response, and parses it."""
    client = get_llm_client(config_loader)
    if not client:
        return None

    # Prepare the generation config from our loaded settings
    gemini_config = config_loader.llm_config.gemini
    gen_config_dict = gemini_config.generation_config.model_dump(exclude_none=True)
    
    # Ensure JSON mode is always enabled
    gen_config_dict["response_mime_type"] = "application/json"
    
    generation_config = genai.types.GenerationConfig(**gen_config_dict)

    print("--- Calling Gemini API for Analysis (REAL) ---")
    try:
        # Pass both the prompt and the generation config to the client
        response = client.generate_content(prompt, generation_config=generation_config)
        
        if config_loader.llm_config.app.debug_mode:
            # --- DEBUGGING: Dump raw JSON response to console ---
            print("\n--- LLM OUTPUT: RAW JSON RESPONSE ---")
            print(response.text)
            print("-------------------------------------\n")

        return LLMAnalysisResult.model_validate_json(response.text)
    except ValidationError as e:
        st.error("The AI's response did not match the required format.")
        st.exception(e)
        st.write("Raw AI Response:")
        st.code(response.text if 'response' in locals() else "No response from AI.", language="json")
        return None
    except Exception as e:
        st.error("An unexpected error occurred while communicating with the Gemini API.")
        st.exception(e)
        return None