# src/portfolio_mapper/data_loader.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
This module is responsible for loading, validating, and preparing all
configuration and framework data from the filesystem.
"""

# --- Python Imports ---

import os
import yaml
from pydantic import ValidationError, BaseModel
from typing import Dict, List, Optional

# --- Local Imports ---

# Import our framework models using relative paths
from .models.framework import FrameworkFile, FrameworkNode

# Import all our config models using relative paths
from .models.config import (
    AcademicLevelsConfig,
    RolesConfig,
    PromptsConfig,
    Role,
    AcademicLevel,
    Prompt,
    LlmConfig,
    AcademicLevelKey,
)

class FrameworkLoader:
    """
    Handles the discovery, loading, validation, and processing of all
    framework YAML files.
    """
    def __init__(self, frameworks_dir: str):
        self.frameworks_dir = frameworks_dir
        self.library: Dict[str, FrameworkFile] = {}
        print("Initializing FrameworkLoader...")

    def load_all(self):
        """
        Main entry point to discover and load all frameworks.
        This is the only method you'll need to call from the outside.
        """
        print(f"--- Starting framework discovery in '{self.frameworks_dir}' ---")
        self._discover_and_load_files()
        self._process_fully_qualified_ids()
        self._check_dependencies()
        print(f"--- Framework loading complete. {len(self.library)} frameworks loaded. ---")
        return self.library

    def _discover_and_load_files(self):
        """
        Scans the directory, validates YAML files against the Pydantic model,
        and populates the initial library.
        """
        for root, _, files in os.walk(self.frameworks_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    framework_code = self._generate_framework_code(file_path)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        
                        data.setdefault('metadata', {})['framework_code'] = framework_code
                        framework_model = FrameworkFile.model_validate(data)
                        self.library[framework_code] = framework_model
                        print(f"  ✅ [LOADED & VALIDATED] {framework_code}")

                    except ValidationError as e:
                        print(f"  ❌ [VALIDATION ERROR] in {file_path}:\n{e}\n")
                    except Exception as e:
                        print(f"  ❌ [LOADING ERROR] in {file_path}: {e}\n")

    def _generate_framework_code(self, file_path: str) -> str:
        """Generates a unique code from a file path."""
        relative_path = os.path.relpath(file_path, self.frameworks_dir)
        path_without_ext = os.path.splitext(relative_path)[0]
        return path_without_ext.replace(os.path.sep, '-').replace('\\', '-')

    def _process_fully_qualified_ids(self):
        """
        Iterates through all loaded frameworks and processes their node IDs
        to be fully qualified paths.
        """
        print("\n--- Processing fully qualified IDs ---")
        for code, framework in self.library.items():
            processed_framework = framework.model_copy(deep=True)
            self._recursive_id_processor(processed_framework.structure)
            self.library[code] = processed_framework
            print(f"  ✅ [PROCESSED] IDs for {code}")

    def _recursive_id_processor(self, nodes: List[FrameworkNode], parent_path: str = ""):
        """Helper function to recursively build fully qualified IDs."""
        for node in nodes:
            current_path = f"{parent_path}:{node.id}" if parent_path else node.id
            node.display_id = node.id
            node.id = current_path
            if node.children:
                self._recursive_id_processor(node.children, current_path)
    
    def _check_dependencies(self):
        """
        Checks that all declared dependencies for each framework exist in the library.
        """
        print("\n--- Verifying framework dependencies ---")
        all_ok = True
        for code, framework in self.library.items():
            if framework.metadata.dependencies:
                for dep_code in framework.metadata.dependencies:
                    if dep_code not in self.library:
                        print(f"  ❌ [MISSING DEPENDENCY] Framework '{code}' depends on '{dep_code}', which was not found or failed to load.")
                        all_ok = False
        if all_ok:
            print("  ✅ [VERIFIED] All framework dependencies are met.")

class ConfigLoader:
    """
    Handles loading and validating all YAML configuration files.
    """
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.roles: Dict[str, Role] = {}
        self.academic_levels: Dict[AcademicLevelKey, AcademicLevel] = {}
        self.prompts: Dict[str, Prompt] = {}
        self.llm_config: Optional[LlmConfig] = None
        print("\nInitializing ConfigLoader...")

    def load_all(self):
        """Loads and validates all known configuration files."""
        print(f"--- Starting configuration loading in '{self.config_dir}' ---")
        self._load_config_file('roles.yaml', RolesConfig, 'roles')
        self._load_config_file('academic_levels.yaml', AcademicLevelsConfig, 'academic_levels')
        self._load_config_file('prompts.yaml', PromptsConfig, 'prompts')

        try:
            llm_config_path = os.path.join(self.config_dir, 'llm_config.yaml')
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self.llm_config = LlmConfig.model_validate(data)
            print(f"  ✅ [LOADED & VALIDATED] llm_config.yaml")
        except FileNotFoundError:
            print(f"  ⚠️ [INFO] 'llm_config.yaml' not found. Using default LLM settings.")
            self.llm_config = LlmConfig.model_validate({"gemini": {"safety_settings": []}})
        except ValidationError as e:
            print(f"  ❌ [FATAL VALIDATION ERROR] in llm_config.yaml:\n{e}\n")
            raise

        self._verify_role_dependencies()
        print("--- Configuration loading complete. ---")

    def _load_config_file(self, filename: str, model: BaseModel, target_attr: str):
        """A generic helper to load and validate a single YAML config file."""
        file_path = os.path.join(self.config_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            validated_data = model.model_validate(data)
            setattr(self, target_attr, getattr(validated_data, target_attr))
            print(f"  ✅ [LOADED & VALIDATED] {filename}")
        except FileNotFoundError:
            print(f"  ❌ [FATAL ERROR] Config file not found: {file_path}")
            raise
        except (ValidationError, Exception) as e:
            print(f"  ❌ [FATAL ERROR] in {filename}: {e}")
            raise

    def _verify_role_dependencies(self):
        """Verifies that the academic levels assigned to roles actually exist."""
        print("--- Verifying role dependencies on academic levels ---")
        error_messages = []
        for role_id, role_data in self.roles.items():
            if role_data.default_academic_level not in self.academic_levels:
                msg = f"Role '{role_id}' refers to non-existent academic level '{role_data.default_academic_level.value}'."
                print(f"  ❌ [INVALID DEPENDENCY] {msg}")
                error_messages.append(f"  - {msg}")

        if error_messages:
            error_summary = "\n".join(error_messages)
            raise ValueError(f"Configuration Error: Role dependencies not met.\n{error_summary}")
        else:
            print("  ✅ [VERIFIED] All roles have valid academic levels.")
