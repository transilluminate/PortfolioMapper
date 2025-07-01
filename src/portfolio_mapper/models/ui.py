# src/portfolio_mapper/models/ui.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

from typing import Dict, List, Set
from pydantic import BaseModel

from .config import Role, AcademicLevel
from .framework import FrameworkFile

class UserSelections(BaseModel):
    """A data model to hold all user selections from the sidebar."""
    role_obj: Role
    level_obj: AcademicLevel
    selected_level_key: str
    next_level_name: str
    next_level_description: str
    available_frameworks: Dict[str, FrameworkFile]
    selected_framework_codes: List[str]
    all_required_codes: Set[str]
    selected_role_display: str
    selected_level_name: str

    class Config:
        arbitrary_types_allowed = True

