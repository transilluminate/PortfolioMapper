# src/portfolio_mapper/models/safety.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import List
from pydantic import BaseModel, Field
from enum import Enum

class SafetyFlag(str, Enum):
    """Specific categories of detected safety issues."""
    USER_DISTRESS_SELF_HARM = "USER_DISTRESS_SELF_HARM"
    # Future flags could be added here, e.g., THREAT_TO_OTHERS

class PiiFlag(str, Enum):
    """Specific categories of detected PII."""
    SPECIFIC_DATE = "specific_date"
    FULL_NAME = "full_name_or_title"
    NHS_OR_MRN_NUMBER = "nhs_or_mrn_number"
    PHONE_NUMBER = "phone_number"
    EMAIL_ADDRESS = "email_address"
    LOCATION = "specific_location_or_ward"
    OTHER = "other"

class PiiDetection(BaseModel):
    """Describes a single piece of detected PII."""
    flag: PiiFlag = Field(description="The category of PII detected.")
    text: str = Field(description="The exact text snippet that was flagged.")
    explanation: str = Field(description="A brief explanation of why this was flagged.")

class SafetyAnalysis(BaseModel):
    """
    The root model for the output of our safety and PII triage call.
    This is the structure we will ask the LLM to return.
    """
    is_safe_for_processing: bool = Field(
        description="True if the text contains no direct personal distress. False otherwise."
    )
    safety_flags: List[SafetyFlag] = Field(
        default_factory=list,
        description="A list of flags indicating the type of safety concern found."
    )
    pii_detections: List[PiiDetection] = Field(
        default_factory=list,
        description="A list of all detected instances of Personally Identifiable Information."
    )