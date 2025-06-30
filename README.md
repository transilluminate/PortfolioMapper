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

## 📄 License

This software is provided under a dual-license model:

-   **MIT License:** For use by the National Health Service (NHS) in the UK.
-   **Commercial License:** For any other commercial use, a separate license is required. Please contact adrian.j.robinson@gmail.com for inquiries.

## 💥 Live Demonstration

A hosted instance is available at: https://portfoliomapper.streamlit.app/

## Sample Input and Output

*Here are some fake reflections and sample AI output. This is formatted better in the app! It's here as a sample of the different academic levels of 'coaching' that the AI provides...*

### Fake Reflection 1 (Trainee Advanced Practitioner in Mental Healh)

Input reflection:

> I was recently asked to support the acute inpatient ward with a case involving 'Tom', a young man with a mild learning disability who was admitted during a mental health crisis. Tom was presenting with extreme anxiety and behaviour that the team found challenging, and he was not engaging with the standard ward routine. The staff felt unequipped to manage his needs, and there was a risk of his distress being seen simply as a component of his learning disability, a classic case of diagnostic overshadowing.
>
> My initial focus was to conduct a comprehensive assessment that accounted for both his acute mental state and his communication needs. I worked alongside the ward team to introduce reasonable adjustments, such as using an easy-read daily planner and a communication passport that we co-developed with Tom's family. This immediately helped reduce his anxiety by making the environment more predictable. I also spent time with the ward nurses, modelling how to adapt their communication and explaining how Tom's anxiety was a separate clinical issue, which required a different approach to his baseline needs.
>
> Following this intervention, Tom's engagement improved significantly, and the ward staff reported feeling more confident in their ability to provide him with appropriate care. The experience highlighted a clear systems-level gap in knowledge. As a result, I am now collaborating with the trust's Learning Disability liaison team to develop a basic 'crisis pack' for ward admissions. This will include templates for communication passports and guidance on making reasonable adjustments, ensuring we provide equitable and effective care for all patients, bridging the gap between mental health and learning disability services.


Output:

> Overall Summary
>
> Your reflection demonstrates a strong understanding of advanced practice principles. You effectively describe a complex case, highlight your insightful interventions, and demonstrate your ability to work collaboratively across professional and organisational boundaries. Your initiative in developing the 'crisis pack' is commendable and shows a commitment to service improvement. To further enhance your reflection and demonstrate mastery-level capabilities, focus on explicitly linking your actions to the evidence base, critically evaluating your decisions and interventions, and exploring the broader systemic factors that influence practice. Well done!
>
> Suggested Matching Competencies
>
> CfAP Advanced: Mental Health (2022): Mental health advanced practice area specific capability and curriculum framework
>
> 1.2: Use appropriate verbal and non-verbal empathic communication that respects the person, addresses any adaptation needs, barriers and inequalities, ensures partnership and shared decision making, and is collaborative, non-discriminatory and non-judgmental.
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection demonstrates advanced practice by describing how the author adapted communication strategies to meet Tom's needs, considering his learning disability and anxiety. The use of 'easy-read daily planner' and 'communication passport' shows an understanding of communication barriers and the implementation of reasonable adjustments to overcome them. The phrase 'modelling how to adapt their communication' and explaining how Tom's anxiety was a separate clinical issue indicates a nuanced approach to communication in a complex situation.
>
> Next Level Evidence: To reach Masters Level, consider explicitly linking your communication strategies to the evidence base. For example, you could cite research on effective communication with individuals with learning disabilities or anxiety. Critically evaluate the effectiveness of your chosen communication methods, reflecting on what worked well, what could have been improved, and how you might adapt your approach in similar situations in the future.
>
> 2.8: Exhibit professional curiosity in undertaking and articulating comprehensive, person-centred history taking and assessment, with a focus on psychological, biological and social perspectives, in line with agreed scope of practice.
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection highlights a comprehensive assessment that considered both Tom's acute mental state and his communication needs. The author's actions demonstrate a person-centred approach by working alongside the ward team and Tom's family to develop a communication passport and easy-read daily planner. This shows a holistic approach to assessment, incorporating psychological, social and communication aspects.
>
> Next Level Evidence: To reach Masters Level, you should critically reflect on the limitations of your assessment and identify areas for improvement. Were there any aspects of Tom's history or presentation that were difficult to assess? How did you manage any uncertainties or ambiguities in the information you gathered? Consider citing relevant literature or guidelines to support your assessment methods.
>
> 3.2: Develop differential judgements, recognising key biases and common errors, including diagnostic overshadowing and the issues relating to diagnosis in the face of ambiguity and incomplete data.
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection explicitly identifies and addresses the risk of 'diagnostic overshadowing', demonstrating an understanding of common biases in assessment. The author's focus on addressing Tom's anxiety as a separate clinical issue, rather than attributing it solely to his learning disability, showcases the ability to make differential judgements in a complex situation.
>
> Next Level Evidence: To reach Masters Level, explore the broader systemic factors that contribute to diagnostic overshadowing. How could the ward's systems or training be improved to reduce this bias? Support your analysis with evidence from relevant literature on diagnostic overshadowing and bias in healthcare.
>
> 4.8: Lead collaboration with an appropriate range of multi-agency and inter-professional resources, developing, maintaining and evaluating links to least restrictive practice and balancing the complexity of risk and safety, across organisations and settings.
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection details the author's collaboration with the ward team, Tom's family, and the trust's Learning Disability liaison team to develop a 'crisis pack' for ward admissions. This demonstrates leadership in developing multi-agency collaborations to improve patient care and address systemic gaps in knowledge and practice.
>
> Next Level Evidence: To reach Masters Level, critically evaluate the effectiveness of your collaborative efforts. What challenges did you encounter in working across different agencies? How did you overcome these challenges? What impact has your intervention had on the wider system? Support your reflections with evidence from relevant literature on inter-professional collaboration and service improvement.
>
> CfAP Advanced: Generic (2025): Multi-professional framework for advanced clinical practice in England
>
> 1.6: use expertise and decision-making skills to inform clinical reasoning approaches when dealing with differentiated and undifferentiated individual presentations and complex situations, synthesising information from multiple sources to make appropriate, evidence-based judgements and diagnoses
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The author's response to Tom's complex presentation, involving both mental health and learning disability, demonstrates advanced clinical reasoning. The reflection shows synthesis of information from multiple sources (assessment, ward staff, family) to inform decisions and interventions. The author's actions show appropriate, evidence-based judgements in a complex situation.
>
> Next Level Evidence: To reach Masters Level, explicitly link your clinical reasoning to the evidence base. Cite relevant research articles or guidelines that support your decisions. Critically evaluate the strengths and limitations of your clinical reasoning process, and identify areas for future development.
>
> 1.9: work collaboratively with an appropriate range of multi-agency and inter-professional resources, developing, maintaining, and evaluating links to manage risk and issues across organisations and settings
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection demonstrates effective collaboration with the ward team, Tom's family, and the Learning Disability liaison team. The author's initiative in developing a 'crisis pack' shows proactive engagement in managing risk and addressing systemic issues across organisational boundaries.
>
> Next Level Evidence: To reach Masters Level, critically evaluate the effectiveness of your collaborative work. What challenges did you face in working across different organisations? How did you overcome these challenges? What impact has your work had on improving services and reducing risk?
>
> 2.5: lead new practice and service redesign solutions in response to feedback, evaluation and need, working across boundaries and broadening sphere of influence
>
> Achieved Level: Advanced Practice (Managing Complexity)
>
> Justification: The reflection describes the author's response to a gap in service provision by leading the development of a 'crisis pack' in collaboration with the Learning Disability liaison team. This demonstrates leadership in initiating service redesign to improve care for patients with learning disabilities and mental health needs.
>
> Next Level Evidence: To reach Masters Level, critically evaluate the impact of your service redesign initiative. How did you measure its success? What challenges did you encounter in implementing the changes? How could the initiative be further developed or improved?


### Fake Reflection 2 (Struggling Pre-registration Nursing Student)

Input reflection:

> Last Tuesday was the worst day. I was trying to help Mr. Smith with his drink, but then Mrs. Jones started shouting that she needed the toilet. I didn't know what to do so I just kind of panicked and rushed to her, but by the time I got there, she had already had an accident. I felt absolutely awful and it was all my fault. Her family came in later and were obviously upset and I could feel them looking at me. I just wanted the floor to swallow me up.
>
> My practice supervisor saw I was upset and asked me what was wrong. I told her about the accident and she said that the ward is busy and these things happen, and that I should have just asked someone else to help me with Mr. Smith's drink. I just nodded but I felt so stupid, like I should have known that. Everyone else seems to know what they're doing and I just feel like I'm getting in the way all the time.
>
> I know I need to be better at managing my time, but I don't know how. I suppose the main thing I learned is that I'm not very good under pressure. My action plan is to try harder to not get so flustered next shift and to remember to ask for help more. I just really hope a situation like that doesn't happen again because I don't know what I'd do.

Output:

> Overall Summary
>
> This reflection demonstrates a developing understanding of key nursing competencies. You show a capacity for self-reflection and a willingness to learn from your mistakes. Your action plan is a good start, but it needs more specific detail and evidence-based strategies. Focus on evaluating the effectiveness of your actions and exploring how you will apply the NMC code and standards to improve your practice. Remember, every experience is an opportunity for growth, and your willingness to reflect is a valuable asset. Keep up the excellent work!
>
> Suggested Matching Competencies
>
> NMC Code (2018): The Code: Professional standards of practice and behaviour for nurses, midwives and nursing associates
>
> Practice effectively
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection shows awareness of the need for effective practice, as evidenced by the student's recognition of their time management issues and their plan to improve. The student's statement, 'I know I need to be better at managing my time, but I don't know how,' shows an understanding of the need for improvement, though they lack concrete strategies. This aligns with the 'Developing' level description: 'The reflection should move from description to application and early analysis...Look for connections being made between theory and practice...' The student attempts to connect theory (time management) to practice, but the connection is weak. The reflection lacks detail on record-keeping (10.1-10.6) and communication (7.1-9.4).
>
> Next Level Evidence: To reach the 'Graduate' level, you need to demonstrate competent practice and evaluation. Provide specific examples of how you applied your knowledge and skills during the incident. Describe your communication with colleagues and how you ensured accurate record-keeping. Evaluate the effectiveness of your actions and the outcomes for the patients involved.
>
> Preserve safety
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection demonstrates awareness of the importance of patient safety, as evidenced by the student's distress over the accident and their desire to avoid similar situations in the future. The student's statement, 'I felt absolutely awful and it was all my fault,' shows a degree of self-awareness regarding the impact of their actions on patient safety. However, the reflection lacks detailed analysis of the risks involved and the steps taken to mitigate them. The student's focus is on their emotional response rather than a systematic analysis of safety procedures (13.1-19.4). This aligns with the 'Developing' level, which focuses on 'early attempts to analyze why things happened the way they did'.
>
> Next Level Evidence: To reach the 'Graduate' level, you need to demonstrate a more thorough understanding of safety procedures. Your reflection should include a detailed analysis of the risks involved in the situation, the actions you took (or should have taken) to mitigate those risks, and an evaluation of the effectiveness of your actions in preserving patient safety. Consider referencing relevant guidelines and policies.
>
> Priorise people
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection demonstrates an understanding of the basic principles of prioritising people's needs, as evidenced by the student's recognition of their failure to meet both Mr. Smith and Mrs. Jones' needs simultaneously. While the reflection focuses on the negative outcome, it shows early attempts to analyse their actions and identify areas for improvement. This aligns with the 'Developing' level description: 'The reflection should move from description to application and early analysis. The user should not only describe what happened, but also explain how they applied their knowledge and skills.' Specifically, the student's statement, 'I suppose the main thing I learned is that I'm not very good under pressure,' indicates an attempt at self-analysis, though it lacks depth and detailed consideration of the relevant standards (1.1-5.5).
>
> Next Level Evidence: To reach the 'Graduate' level, your reflection should move beyond describing the event and analysing your actions to evaluating the effectiveness of your response and the outcomes for the patients. Consider what you could have done differently to improve the situation and what you have learned about your decision-making processes in similar situations. You could also explore how you will apply the NMC code of conduct to similar situations in the future.
>
> Promote professionalism and trust
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection shows some awareness of the importance of professionalism, as evidenced by the student's self-critique and their intention to improve. The student's statement, 'I just really hope a situation like that doesn't happen again because I don't know what I'd do,' demonstrates a desire to improve their competence. However, the reflection lacks detailed discussion of how they will uphold professional standards and maintain trust with patients (20 1-25.2). This aligns with the 'Developing' level, which focuses on 'early attempts to analyze why things happened the way they did'.
>
> Next Level Evidence: To reach the 'Graduate' level, your reflection should demonstrate a deeper understanding of professional responsibilities and how your actions contribute to building trust with patients. Consider how you will apply the principles of professionalism in future situations and how you will learn from this experience to improve your practice.
>
> NMC Standards (2024): Standards of proficiency for registered nurses
>
> 1.1: understand and act in accordance with 'The Code: Professional standards of practice and behaviour for nurses, midwives and nursing associates', and fulfil all registration requirements
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection shows a developing understanding of the NMC code, as the student's supervisor suggests asking for help, which is in line with the code. However, the student's emotional response and lack of proactive problem-solving indicate a need for further development in this area.
>
> Next Level Evidence: To reach the next level, explicitly discuss how you will apply the NMC code in future situations, providing specific examples of how you will act in accordance with its principles.
>
> 1.11: communicate effectively using a range of skills and strategies with colleagues and people at all stages of life and with a range of mental, physical, cognitive and behavioural health challenges
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection highlights a communication breakdown, but doesn't explore effective communication strategies. The student's response to the supervisor was passive, suggesting a need for improvement in assertive communication.
>
> Next Level Evidence: To improve, discuss how you would communicate more effectively in similar situations. Consider different communication strategies and how they could have improved the outcome. Reflect on the importance of assertive communication with colleagues.
>
> 1.16: demonstrate the ability to keep complete, clear, accurate and timely records
>
> Achieved Level: Foundational (Year 1 Student)
>
> Justification: The reflection doesn't mention record-keeping practices. This is a fundamental aspect of nursing practice, and the lack of discussion indicates a foundational level of understanding.
>
> Next Level Evidence: To progress, discuss how you would ensure complete, clear, accurate and timely record-keeping in this situation. What information would you have documented, and how would you ensure its accuracy?
>
> 1.3: understand and apply the principles of courage, transparency and the professional duty of candour, recognising and reporting any situations, behaviours or errors that could result in poor care outcomes
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The student acknowledges their error and expresses remorse, indicating an understanding of the need for candour. However, the reflection lacks a detailed analysis of the situation and how transparency could have improved the outcome.
>
> Next Level Evidence: To progress, reflect on how you could have approached the situation with more courage and transparency. Consider what steps you would take to report such incidents to ensure learning and prevent future occurrences.
>
> 3.15: demonstrate the ability to work in partnership with people, families and carers to continuously monitor, evaluate and reassess the effectiveness of all agreed nursing care plans and care, sharing decision-making and readjusting agreed goals, documenting progress and decisions made
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection shows some awareness of the need for partnership working, but it lacks detail on how this was implemented. The student's focus is primarily on their own failings, rather than a collaborative approach to care.
>
> Next Level Evidence: To progress, reflect on how you could have involved Mr. Smith and Mrs. Jones more in the decision-making process. Discuss how you would work in partnership with patients and their families to monitor and evaluate the effectiveness of care plans.
>
> 4.10: demonstrate the knowledge and ability to respond proactively and promptly to signs of deterioration or distress in mental, physical, cognitive and behavioural health and use this knowledge to make sound clinical decisions
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection shows the student recognised Mrs. Jones' distress, but their response was reactive rather than proactive. They panicked instead of implementing a plan to address the situation effectively.
>
> Next Level Evidence: To progress, discuss how you could have responded more proactively to Mrs. Jones' needs. What steps could you have taken to prevent the accident, and how would you improve your decision-making in similar situations?
>
> 6.8: demonstrate an understanding of how to identify, report and critically reflect on near misses, critical incidents, major incidents and serious adverse events in order to learn from them and influence their future practice
>
> Achieved Level: Developing (Mid-to-late stage Student)
>
> Justification: The reflection demonstrates the student's understanding of the seriousness of the incident. However, it lacks detail on formal reporting procedures or a critical analysis of the event to inform future practice.
>
> Next Level Evidence: To progress, discuss the formal reporting procedures you would follow in such an incident. Critically analyse the event, identifying contributing factors and suggesting strategies for improvement.
