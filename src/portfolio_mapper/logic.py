# src/portfolio_mapper/logic.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
This module contains the core business logic of the application, such as
data transformations and prompt assembly, independent of the UI.
"""
import fnmatch
import json
from typing import Dict, List, Any

from .models.framework import FrameworkFile, FrameworkNode
from .models.config import Role, AcademicLevel, Prompt, AcademicLevelKey
from .models.llm_response import LLMAnalysisResult
from .models.safety import SafetyAnalysis

def resolve_allowed_frameworks(
    role_obj: Role, 
    framework_library: Dict[str, FrameworkFile]
) -> Dict[str, FrameworkFile]:
    """
    Resolves a role's allowed framework codes, expanding any wildcards.
    """
    allowed_codes = set()
    all_available_codes = framework_library.keys()
    
    for pattern in role_obj.allowed_framework_codes:
        if "*" in pattern or "?" in pattern:
            matching_codes = fnmatch.filter(all_available_codes, pattern)
            allowed_codes.update(matching_codes)
        else:
            if pattern in all_available_codes:
                allowed_codes.add(pattern)
            else:
                print(f"Warning: Role '{role_obj.display_name}' refers to non-existent framework '{pattern}'.")

    return {
        code: framework_library[code] 
        for code in sorted(list(allowed_codes))
    }

def _get_all_leaf_nodes(nodes: List[FrameworkNode]) -> List[tuple[str, str]]:
    """Recursively traverses nodes to find all leaf nodes (nodes with no children)."""
    leaf_nodes = []
    for node in nodes:
        if not node.children:
            display_id = node.display_id if node.display_id else node.id
            leaf_nodes.append((display_id, node.text))
        else:
            leaf_nodes.extend(_get_all_leaf_nodes(node.children))
    return leaf_nodes

def _recursive_prune_nodes(nodes: List[FrameworkNode], academic_level_key: str) -> List[FrameworkNode]:
    """
    Recursively processes framework nodes, pruning and tailoring them
    based on the provided academic level.
    """
    pruned_nodes = []
    for node in nodes:
        node_copy = node.model_copy(deep=True)
        
        if node_copy.collapse_children and node_copy.children:
            descendant_leaf_nodes = _get_all_leaf_nodes(node_copy.children)
            if node_copy.source_notes is None:
                node_copy.source_notes = []

            if descendant_leaf_nodes:
                # Add a clear introductory note.
                node_copy.source_notes.append("This principle is demonstrated by evidence of the following points:")
                
                # Add each child statement as a separate, structured note.
                sorted_leaf_nodes = sorted(descendant_leaf_nodes, key=lambda x: x[0])
                for stmt_id, stmt_text in sorted_leaf_nodes:
                    node_copy.source_notes.append(f"- {stmt_text} (ID: {stmt_id})")
            
            # Automatically set the instruction for collapsed nodes.
            node_copy.llm_instructions = f"This is a high-level principle. If you match this node, you MUST use its 'display_id' ('{node_copy.display_id}') for the 'competency_id' in your response. In your 'justification_for_level', you should then reference the most relevant supporting competency IDs (e.g., 'ID: 1.1', 'ID: 6.2') to support your reasoning."
            
            node_copy.children = None
            node_copy.collapse_children = False

        if node_copy.children:
            # If a node still has children at this point, it is an intermediate
            # grouping node (e.g., a Domain or Competency). We must explicitly
            # forbid the AI from matching it to force it to look deeper.
            node_copy.llm_instructions = "This is a category/domain, not a specific competency. Do not match this node directly. You must find a more specific match within its children."

            pruned_children = _recursive_prune_nodes(node_copy.children, academic_level_key)
            node_copy.children = pruned_children if pruned_children else None

        pruned_nodes.append(node_copy)
            
    return pruned_nodes

def prune_framework_for_llm(framework: FrameworkFile, academic_level_key: AcademicLevelKey) -> Dict[str, Any]:
    """
    Creates a pruned and tailored dictionary representation of a framework
    for inclusion in the LLM prompt.
    """
    pruned_fw = framework.model_copy(deep=True)
    pruned_fw.structure = _recursive_prune_nodes(pruned_fw.structure, academic_level_key.value)
    return pruned_fw.model_dump(exclude_none=True)

def assemble_safety_prompt(
    reflection_text: str,
    prompt_obj: Prompt,
) -> str:
    """
    Assembles the prompt for the initial safety and PII check.
    """
    print("--- Assembling Safety Check Prompt ---", flush=True)
    output_schema = json.dumps(SafetyAnalysis.model_json_schema(), indent=2)

    return prompt_obj.template.format(
        user_reflection_text=reflection_text,
        output_schema=output_schema,
    )

def assemble_analysis_prompt(
    role_obj: Role,
    academic_level_obj: AcademicLevel,
    academic_level_key: AcademicLevelKey,
    reflection_text: str,
    selected_frameworks: Dict[str, FrameworkFile],
    prompt_obj: Prompt,
    next_level_name: str,
    next_level_description: str,
    debug_mode: bool,
    all_academic_levels: Dict[AcademicLevelKey, AcademicLevel]
) -> str:
    """
    Assembles the final, massive prompt string to send to the LLM.
    """
    print("--- Assembling Analysis Prompt ---", flush=True)

    output_schema = json.dumps(LLMAnalysisResult.model_json_schema(), indent=2)

    academic_levels_json = json.dumps(
        {k.value: v.model_dump() for k, v in all_academic_levels.items()}, 
        indent=2
    )
    
    pruned_frameworks = [
        prune_framework_for_llm(fw, academic_level_key)
        for fw in selected_frameworks.values()
    ]
    frameworks_json_string = json.dumps(pruned_frameworks, indent=2)

    if debug_mode:
        print("\n--- LLM INPUT: FRAMEWORKS JSON ---", flush=True)
        print(frameworks_json_string, flush=True)
        print("\n--- LLM INPUT: OUTPUT SCHEMA JSON ---", flush=True)
        print(output_schema, flush=True)
        print("------------------------------------\n", flush=True)

    return prompt_obj.template.format(
        tone=prompt_obj.tone or "",
        persona=prompt_obj.persona or "",
        role_display_name=role_obj.display_name,
        academic_level_name=academic_level_obj.name,
        academic_level_description=academic_level_obj.description,
        user_reflection_text=reflection_text,
        frameworks_json_string=frameworks_json_string,
        output_schema=output_schema,
        next_level_name=next_level_name,
        next_level_description=next_level_description,
        academic_levels_json=academic_levels_json
    )
