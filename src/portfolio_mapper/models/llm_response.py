# src/portfolio_mapper/models/llm_response.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import List, Optional
from pydantic import BaseModel, Field

class AssessedCompetency(BaseModel):
    """
    Represents a single competency that the LLM has assessed based on the user's reflection.
    """
    framework_code: str = Field(
        ..., 
        description="The unique code of the framework this competency belongs to (e.g., 'RPS-2021-prescribing-v1')."
    )
    competency_id: str = Field(
        ..., 
        description="The user-friendly display ID of the competency node (e.g., 'prioritise_people' or '1.1')."
    )
    competency_text: str = Field(
        ...,
        description="The descriptive text of the competency node."
    )
    achieved_level: str = Field(
        ...,
        description="The academic level (e.g., 'Masters', 'Advanced') the user's reflection demonstrates for this specific competency."
    )
    justification_for_level: str = Field(
        ...,
        description="A detailed justification, quoting from the user's reflection, explaining why the achieved level was assigned."
    )
    emerging_evidence_for_next_level: Optional[str] = Field(
        None,
        description="Constructive feedback on what the user could do or add to their reflection to demonstrate the next academic level for this competency."
    )

class LLMAnalysisResult(BaseModel):
    """
    The root model for the structured JSON response expected from the LLM.
    """
    assessed_competencies: List[AssessedCompetency]
    overall_summary: str = Field(
        ...,
        description="A high-level, holistic summary of the user's reflection, providing overall feedback and encouragement."
    )
