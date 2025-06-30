# src/portfolio_mapper/models/config.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other commercial use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

# --- Academic Levels ---
# This Enum provides type-safe keys for use in other models
class AcademicLevelKey(str, Enum):
    FOUNDATIONAL = "foundational"
    DEVELOPING = "developing"
    GRADUATE = "graduate"
    ADVANCED = "advanced"
    MASTERS = "masters"
    DOCTORAL = "doctoral"

class AcademicLevel(BaseModel):
    name: str = Field(description="The display name of the level, e.g., 'Masters'.")
    description: str = Field(description="The detailed expectation for this level, used to guide the LLM.")

class AcademicLevelsConfig(BaseModel):
    academic_levels: Dict[AcademicLevelKey, AcademicLevel]

# --- Roles ---
class Role(BaseModel):
    display_name: str
    allowed_framework_codes: List[str] = Field(description="A list of framework_codes this role is permitted to see and use.")
    default_academic_level: AcademicLevelKey

class RolesConfig(BaseModel):
    # Key is the role id, e.g., "student_ap"
    roles: Dict[str, Role]

# --- Prompts ---
class Prompt(BaseModel):
    template: str
    persona: str
    tone: str

class PromptsConfig(BaseModel):
    # Key is the prompt name, e.g., "portfolio_analysis_v1"
    prompts: Dict[str, Prompt]

# --- App Configuration ---
class AppConfig(BaseModel):
    """Holds general application settings."""
    debug_mode: bool = Field(False, description="If true, print detailed debugging info to the console.")
    min_reflection_length: int = 150

# --- LLM Configuration ---
class GeminiSafetySetting(BaseModel):
    category: str
    threshold: str

class GeminiGenerationConfig(BaseModel):
    """Defines parameters that control the model's output generation."""
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Controls randomness. Lower is more deterministic.")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling.")
    top_k: Optional[int] = Field(None, ge=1, description="Top-k sampling.")

class GeminiConfig(BaseModel):
    """Holds all settings specific to the Gemini model."""
    model_name: str = Field(default="gemini-1.5-flash-latest", description="The specific Gemini model to use.")
    safety_settings: List[GeminiSafetySetting]
    generation_config: GeminiGenerationConfig = Field(default_factory=GeminiGenerationConfig)

class LlmConfig(BaseModel):
    """The root model for the entire LLM configuration file."""
    app: AppConfig = Field(default_factory=AppConfig)
    gemini: GeminiConfig