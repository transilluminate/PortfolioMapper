from typing import List, Optional
from pydantic import BaseModel, Field

class CompetencyMatch(BaseModel):
    """
    Represents a single row in the output mapping table, linking a piece of
    the reflection to a specific competency.
    """
    framework_short_title: str = Field(..., description="The short title of the framework, e.g., 'RPS' or 'CfAP AP'.")
    competency_id: str = Field(
        ...,
        description="The full, unique identifier for the competency, including its path. Example: '[RPS:The Consultation:1.1]'"
    )
    justification: str = Field(
        ...,
        description="A detailed explanation of why the clinical reflection maps to this competency, quoting specific parts of the reflection."
    )
    strength_of_match: int = Field(
        ...,
        description="A score from 1 (weak link) to 5 (very strong, direct evidence) indicating the strength of the mapping.",
        ge=1,
        le=5
    )
    improvement_suggestion: Optional[str] = Field(
        None,
        description="If the match is weak (e.g., strength 1-3), provide a suggestion on how to strengthen the reflection to better evidence this specific competency. For strong matches, this can be null."
    )

class PotentialCompetency(BaseModel):
    """
    Represents a competency that was NOT matched but could be if the reflection
    was expanded upon. This is for identifying growth opportunities.
    """
    framework_short_title: str = Field(..., description="The short title of the framework, e.g., 'RPS' or 'CfAP AP'.")
    competency_id: str = Field(
        ...,
        description="The full, unique identifier for the potential competency. Example: '[CfAP AP:Leadership and Management:2.8]'"
    )
    suggestion: str = Field(
        ...,
        description="A specific suggestion on what to add or expand upon in the reflection to meet this potential competency. Frame this as a constructive opportunity."
    )


class MappingResult(BaseModel):
    """
    The top-level object that the LLM must return. It contains a summary and a
    list of all identified competency matches.
    """
    summary: str = Field(
        ..., description="A brief, high-level summary of how the reflection maps to the frameworks overall."
    )
    matches: List[CompetencyMatch] = Field(
        ..., description="A list of all competency matches found in the reflection.", alias="matches"
    )
    potential_matches: List[PotentialCompetency] = Field(
        default_factory=list,
        description="A list of high-potential competencies not currently met but could be with additional reflection. Identify up to 3 key opportunities.",
        alias="potential_matches"
    )
