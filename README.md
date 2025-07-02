[<img src="https://img.shields.io/badge/License_(for_the_NHS)-MIT-yellow">](https://github.com/transilluminate/PortfolioMapper?tab=readme-ov-file#-license) [<img src="https://img.shields.io/badge/License_(for_others)-Commercial-blue">](https://github.com/transilluminate/PortfolioMapper?tab=readme-ov-file#-license) 

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
-   **Integrated Safety & Privacy:** Automatically screens reflections for user distress and personally identifiable information (PII) before full analysis, empowering the user and ensuring responsible AI use.

## 🏛️ Architecture

The project is structured as a standard Python package to ensure maintainability and scalability. The core logic is separated into distinct, single-responsibility modules.

```
PortfolioMapper/ 
├── .streamlit/ 
│   └── secrets.toml            # For API keys
├── config/                     # User-facing configuration files
│   ├── academic_levels.yaml
│   ├── llm_config.yaml
│   ├── prompts.yaml
│   └── roles.yaml
├── frameworks/                 # Competency framework definitions
│   └── ...
├── src/                        # Source code package
│   └── portfolio_mapper/       # The main Python package
│       ├── app.py              # Main application orchestrator
│       ├── data_loader.py      # Loads and validates all YAML data
│       ├── logic.py            # Core business logic and prompt assembly
│       ├── llm_functions.py    # Handles communication with the Gemini API
│       ├── reporting.py        # Generates PDF reports
│       ├── state_manager.py    # Centralizes all session state logic
│       ├── ui_components.py    # Contains all UI rendering functions
│       ├── analytics.py        # Optional usage logging (anonymous)
│       └── models/             # Pydantic models for data validation
│           └── ...
└── portfolio_mapper.app.py     # The application launcher script
```

-   **`portfolio_mapper.app.py`**: The entry point for Streamlit. It correctly imports and runs the application as a package.
-   **`app.py`**: The orchestrator. It manages the high-level application flow, calling UI components and the analysis pipeline as needed.
-   **`data_loader.py`**: Responsible for finding, loading, and validating all framework and configuration YAML files using Pydantic models.
-   **`logic.py`**: The "brain" of the application. It contains the crucial logic for pruning frameworks based on context and programmatically assembling the final, detailed prompt for the LLM.
-   **`llm_functions.py`**: A dedicated module for interacting with the Google Gemini API. It handles client initialization, API calls, and response parsing.
-   **`reporting.py`**: Contains all logic for generating downloadable files, such as the PDF and CSV reports.
-   **`state_manager.py`**: Centralizes all Streamlit session state initialization and callback logic.
-   **`ui_components.py`**: Contains all the functions responsible for rendering the Streamlit UI, keeping the view logic separate from the application flow.
-   **`analytics.py`**: Sends anonymous usage data to an external Supabase database.
-   **`models/`**: A sub-package containing all Pydantic models, which provide robust data validation and type-safety for all configuration and API response data.

## 🧠 Key Concepts

### The Pedagogical Harness

A key innovation in this project is that it acts as a **"Pedagogical Harness"** for the underlying AI. The code's primary role is to act as a coordinator, assembling multiple layers of human-defined rules and data to provide a scaffold for the LLM. This ensures a pedagogically-aligned analysis on every run.

This is achieved through several layers of programmatic constraint:

1.  **The Master Prompt:** A master directive sets the "rules of engagement," forcing the AI to act exclusively as an expert clinical educator with a professional, constructive tone.
2.  **Structured Frameworks:** Professional frameworks are encoded into a universal, machine-readable format (YAML). This provides a hard boundary for the AI, focusing it solely on the required standards.
3.  **Programmatic Instruction Injection:** The application's logic intelligently processes the framework data before sending it to the AI. It identifies nodes that shouldn't be matched (e.g., parent domains) and programmatically injects instructions to forbid the AI from selecting them. This forces the AI to always match the most granular, specific competency available.

### The Academic Levels Idea

The application assesses reflections on two axes: **what** was done (competency matching) and **how well** it was reflected upon (academic level). The `config/academic_levels.yaml` file defines a clear, pre-defined rubric that the AI uses to evaluate the depth of critical thinking in the user's writing.

This allows the tool to provide much more nuanced feedback. It can recognize, for example, that a reflection might demonstrate a specific competency but only at a "Foundational" level (describing what happened) rather than a "Doctoral" level (critiquing the system and generating new knowledge). This concept is central to the tool's ability to provide meaningful developmental feedback.

### Integrated Safety & Privacy

Before any reflection is sent for detailed competency analysis, it undergoes a two-stage safety check:

1.  **User Wellbeing:** The app first screens the text for any signs of direct, personal distress or self-harm intent from the author. If such content is detected, the analysis is halted, and the user is presented with resources for support. This is a critical step for responsible AI implementation.
2.  **PII Detection:** The text is then scanned for Personally Identifiable Information (e.g., full names, specific dates, ID numbers). The system is designed to be conservative to avoid false positives. If potential PII is found, the user is shown a warning and must review the items before they can proceed, empowering them to create properly anonymised portfolio entries.

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

5.  **Set up analytics (Optional):**
    -   Create a Supabase database (free tier is sufficient).
    -   In the Supabase SQL Editor, create a table for events:
        ```sql
        CREATE TABLE events (
            id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            event_name TEXT NOT NULL,
            properties JSONB
        );
        ```
    -   Add your Supabase connection string to `.streamlit/secrets.toml`:
        ```toml
        # Supabase connection for analytics
        [connections.db]
        url = "postgresql://postgres_url_from_supabase_including_password"
        ```

6.  **Run the application:**
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

## 📄 License

This software is provided under a dual-license model:

-   **MIT License:** For use by the National Health Service (NHS) in the UK.
-   **Commercial License:** For any other use, a separate license is required. Please contact adrian.j.robinson@gmail.com for inquiries.

## 🎥 Watch in Action

https://github.com/user-attachments/assets/c1d8bd53-fc14-4e01-b32e-7298cfc6b8f2

### Fake reflection for this demonstration:

> I was recently asked to support the acute inpatient ward with a case involving 'Tom' (pseudonym), a young man with a mild learning disability who was admitted during a mental health crisis. Tom was presenting with extreme anxiety and behaviour that the team found challenging, and he was not engaging with the standard ward routine. The staff felt unequipped to manage his needs, and there was a risk of his distress being seen simply as a component of his learning disability, a classic case of diagnostic overshadowing.
>
> My initial focus was to conduct a comprehensive assessment that accounted for both his acute mental state and his communication needs. I worked alongside the ward team to introduce reasonable adjustments, such as using an easy-read daily planner and a communication passport that we co-developed with Tom's family. This immediately helped reduce his anxiety by making the environment more predictable. I also spent time with the ward nurses, modelling how to adapt their communication and explaining how Tom's anxiety was a separate clinical issue, which required a different approach to his baseline needs.
>
> Following this intervention, Tom's engagement improved significantly, and the ward staff reported feeling more confident in their ability to provide him with appropriate care. The experience highlighted a clear systems-level gap in knowledge. As a result, I am now collaborating with the trust's Learning Disability liaison team to develop a basic 'crisis pack' for ward admissions. This will include templates for communication passports and guidance on making reasonable adjustments, ensuring we provide equitable and effective care for all patients, bridging the gap between mental health and learning disability services.

### Output Excerpt:

> CfAP Advanced: Mental Health (2022): Mental health advanced practice area specific capability and curriculum framework
>
> (3.2) 'Develop differential judgements, recognising key biases and common errors, including diagnostic overshadowing and the issues relating to diagnosis in the face of ambiguity and incomplete data'
> 
> Match strength: 4/5
> 
> Achieved Level: Advanced (Managing Complexity)
> 
> Jusitification: The reflection explicitly mentions 'diagnostic overshadowing' and the actions taken to mitigate this risk, demonstrating an awareness of potential biases and errors in diagnosis, aligning with the 'Advanced' level's focus on managing complexity. The user states, "The staff felt unequipped to manage his needs, and there was a risk of his distress being seen simply as a component of his learning disability, a classic case of diagnostic overshadowing."
> 
> Emerging evidence for next level: To reach the 'Masters Level', consider critically analysing the systemic factors that contribute to diagnostic overshadowing within the trust. You could explore relevant literature or guidelines to inform your approach and evaluate the effectiveness of the 'crisis pack' in addressing this issue.

Downloaded full CSV output for the demo: [sample_portfolio_analysis.csv](https://github.com/user-attachments/files/21023731/sample_portfolio_analysis.csv)

## 💥 Live App Instance

A hosted live app instance is available at: https://portfoliomapper.streamlit.app/

I may run out of [free-tier resources](https://ai.google.dev/gemini-api/docs/rate-limits#current-rate-limits) with the API calls... check back later if so!
