# 🗺️ AI-Powered Portfolio Mapper

An intelligent Streamlit application designed to help healthcare professionals map their clinical reflections against multiple professional competency frameworks simultaneously using generative AI.

## Overview

This tool provides a sophisticated way for practitioners to gain insight into how their written reflections demonstrate competency across various professional standards (e.g., NMC, RPS, CfAP). Instead of manually cross-referencing documents, a user can submit a single piece of reflective writing, and the application will:

1.  Identify the relevant competencies demonstrated in the text.
2.  Assess the *academic level* of the reflection against a configurable rubric.
3.  Provide structured, justified feedback and guidance for improvement.
4.  Generate downloadable PDF and CSV reports for portfolio evidence.

## ✨ Key Features

-   **Dynamic Framework Mapping:** Competency frameworks are dynamically loaded and filtered based on the user's selected role.
-   **Configurable & Extensible:** New roles, frameworks, and academic levels can be added easily by editing simple YAML files, with no code changes required.
-   **Programmatic Prompt Engineering:** The application intelligently injects specific instructions into the data sent to the LLM, ensuring consistent and accurate analysis across different framework structures.
-   **Nuanced AI Assessment:** The AI evaluates reflections not just for content but for depth and critical thinking, using a configurable academic scale.
-   **Stateful UI:** The interface intelligently disables buttons to prevent duplicate API calls and provides clear user feedback.
-   **Downloadable Reports:** Generate professional PDF and CSV summaries of the analysis for inclusion in a professional portfolio.

## 🏛️ Architecture

The project is structured as a standard Python package to ensure maintainability and scalability. The core logic is separated into distinct, single-responsibility modules.

```
PortfolioMapper/
├── .streamlit/
│   └── secrets.toml      # For API keys
├── config/               # User-facing configuration files
│   ├── academic_levels.yaml
│   ├── llm_config.yaml
│   ├── prompts.yaml
│   └── roles.yaml
├── frameworks/           # Competency framework definitions
│   └── ...
├── src/
│   └── portfolio_mapper/ # The main Python package
│       ├── __init__.py
│       ├── app.py        # Main Streamlit UI and application flow
│       ├── data_loader.py# Loads and validates all YAML data
│       ├── logic.py      # Core business logic and prompt assembly
│       ├── llm_functions.py # Handles communication with the Gemini API
│       ├── reporting.py  # Generates PDF and CSV reports
│       └── models/       # Pydantic models for data validation
│           └── ...
└── run_app.py            # The application launcher script
```

-   **`portfolio_mapper.app.py`**: The entry point for Streamlit. It correctly imports and runs the application as a package.
-   **`app.py`**: The orchestrator. It manages the user interface, session state, and the overall application flow. It delegates all heavy lifting to other modules.
-   **`data_loader.py`**: Responsible for finding, loading, and validating all framework and configuration YAML files using Pydantic models.
-   **`logic.py`**: The "brain" of the application. It contains the crucial logic for pruning frameworks based on context and programmatically assembling the final, detailed prompt for the LLM.
-   **`llm_functions.py`**: A dedicated module for interacting with the Google Gemini API. It handles client initialization, API calls, and response parsing.
-   **`reporting.py`**: Contains all logic for generating downloadable files, such as the PDF and CSV reports.
-   **`models/`**: A sub-package containing all Pydantic models, which provide robust data validation and type-safety for all configuration and API response data.

## 🧠 Key Concepts

### Programmatic Prompt Engineering

A key innovation in this project is the move away from hardcoding complex instructions in the prompt configuration. Instead, the `logic.py` module dynamically processes the framework data before sending it to the AI:

1.  **For Collapsed Nodes (`collapse_children: true`):** The logic automatically gathers all child statements, embeds them as context for the parent, and injects a forceful instruction telling the AI it **must** use the parent's ID in its response.
2.  **For Nested Hierarchies:** The logic identifies any intermediate node (a node that still has children) and programmatically adds an instruction forbidding the AI from matching it directly.

This approach forces the AI to always match the most granular, specific competency available and ensures consistent behavior across all frameworks, all without cluttering the YAML files with boilerplate instructions.

### The Academic Levels Idea

The application assesses reflections on two axes: **what** was done (competency matching) and **how well** it was reflected upon (academic level). The `config/academic_levels.yaml` file defines a rubric that the AI uses to evaluate the depth of critical thinking in the user's writing.

This allows the tool to provide much more nuanced feedback. It can recognize, for example, that a reflection might demonstrate a specific competency but only at a "Foundational" level (describing what happened) rather than a "Doctoral" level (critiquing the system and generating new knowledge). This concept is central to the tool's ability to provide meaningful developmental feedback.

## 🚀 Getting Started

### Prerequisites

-   Python 3.9+
-   A Google Gemini API Key

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd PortfolioMapper
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Key:**
    -   Create a file at `.streamlit/secrets.toml`.
    -   Add your API key to this file:
        ```toml
        GOOGLE_API_KEY = "your_api_key_here"
        ```
    -   Don't forget to add this to `.gitignore`:
        ```
        .streamlit/secrets.toml
        ```

5.  **Run the application:**
    From the project root directory, run the launcher script:
    ```bash
    streamlit run portfolio_mapper.app.py
    ```

## 🔧 Configuration

The application is highly configurable via YAML files in the `config/` and `frameworks/` directories.

-   **`config/roles.yaml`**: Define user roles and specify which frameworks they are allowed to access.
-   **`config/academic_levels.yaml`**: Define the rubric for assessing the quality of reflection.
-   **`config/prompts.yaml`**: Modify the master prompt template sent to the AI.
-   **`config/llm_config.yaml`**: Tweak application settings (like `min_reflection_length`) and LLM generation parameters (like `temperature`).
-   **`frameworks/`**: Add new competency frameworks by creating new YAML files that conform to the Pydantic models defined in `src/portfolio_mapper/models/framework.py`.

## 💥 Demonstration

A hosted instance is available at: https://portfoliomapper.streamlit.app/

## 📄 License

This software is provided under a dual-license model:

-   **MIT License:** For use by the National Health Service (NHS) in the UK.
-   **Commercial License:** For any other commercial use, a separate license is required. Please contact adrian.j.robinson@gmail.com for inquiries.

