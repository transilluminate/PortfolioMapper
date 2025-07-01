# src/portfolio_mapper/models/framework.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import List, Optional
from pydantic import BaseModel, Field

class FrameworkMetadata(BaseModel):
    framework_code: Optional[str] = Field(None, description="Auto-generated unique code from file path.")
    organisation: str
    title: str
    date: str
    abbreviation: str
    display_in_ui: Optional[bool] = Field(True, description="If false, this framework will not be shown in the user selection UI.")
    version: Optional[str] = None
    dependencies: Optional[List[str]] = Field(None)
    source_url: Optional[str] = None

class FrameworkNode(BaseModel):
    id: str
    node_type: str
    text: str
    display_id: Optional[str] = Field(None, description="A user-friendly, concise ID for display purposes, e.g., '1.1'.")
    source_notes: Optional[List[str]] = None
    source_examples: Optional[List[str]] = None
    llm_instructions: Optional[str] = Field(None, description="Qualitative hints for the LLM on how to interpret this node's text.")
    children: Optional[List['FrameworkNode']] = None
    collapse_children: Optional[bool] = Field(False, description="If true, embed child leaf nodes into this node's text and prune them from the structure sent to the LLM.")

class FrameworkFile(BaseModel):
    metadata: FrameworkMetadata
    source_notes: Optional[List[str]] = None
    structure: List[FrameworkNode]

FrameworkNode.model_rebuild()