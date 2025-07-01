# src/portfolio_mapper/models/llm_response.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import List, Optional
from pydantic import BaseModel, Field

class AssessedCompetency(BaseModel):
    """
    Describes a single competency that the LLM has assessed against the reflection.
    """
    framework_code: str = Field(description="The unique code of the framework this competency belongs to.")
    competency_id: str = Field(description="The display_id of the matched competency node.")
    competency_text: str = Field(description="The verbatim text of the matched competency.")
    match_strength: int = Field(
        description="A rating from 1 (weakest) to 5 (strongest) indicating the strength of the evidence for this match.",
        ge=1, le=5
    )
    achieved_level: str = Field(
        description="The name of the academic level the user's evidence has achieved for this competency."
    )
    justification_for_level: str = Field(
        description="A detailed justification for the assigned level, quoting from the user's reflection."
    )
    emerging_evidence_for_next_level: Optional[str] = Field(
        None,
        description="Constructive feedback on how to reach the next academic level for this competency."
    )

class LLMAnalysisResult(BaseModel):
    """
    The root model for the main portfolio analysis response from the LLM.
    """
    overall_summary: str = Field(
        description="A high-level summary of the reflection's strengths and areas for development."
    )
    assessed_competencies: List[AssessedCompetency] = Field(
        description="A list of all competencies found to be evidenced in the reflection."
    )
