## 🗺️ AI Portfolio Mapper

This Streamlit application leverages Google's Gemini AI to help clinical professionals map their reflective practice against various professional competency frameworks. It provides a structured, AI-powered tool to identify demonstrated competencies and areas for growth, outputting results in an interactive, editable table with CSV download options. Your reflection data is processed in real-time and is not stored by the application.

### Demonstration:

A hosted instance is available at [https://portfoliomapper.streamlit.app/](https://portfoliomapper.streamlit.app/).

Note: I may run out of API calls at some point! :D

### Key Benefits:

-   **Intelligent Schema Handling:** Automatically combines generic and profession-specific HCPC competencies for a comprehensive mapping.
-   **Structured Output:** Generates structured JSON output conforming to Pydantic models, ensuring data integrity.
-   **Interactive Results Table:** Displays competency matches and potential growth areas in an editable Streamlit `data_editor` table.
-   **CSV Download:** Easily download mapped competencies and growth areas as CSV files.
-   **User-Friendly Interface:** Clear, step-by-step input process and persistent status updates.


### 🛠️ Setup and Installation (Local):

To run this application locally, follow these steps:

1.  **Clone the Repository:**
    Clone the GitHub repository to your local machine and navigate into the project directory.

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies. Create one using `python3 -m venv .venv` and then activate it (e.g., `source .venv/bin/activate` on Linux/macOS or `.venv\Scripts\activate` on Windows).

3.  **Install Dependencies:**
    Install all required Python packages using `pip install streamlit pandas google-generativeai pydantic`.

4.  **Set Up Google Gemini API Key:**
    This application uses the Google Gemini API.
    *   Go to Google AI Studio to obtain your `GOOGLE_API_KEY`. If you encounter issues, ensure the "Vertex AI API" is enabled in your Google Cloud Project associated with the key.
    *   Create a `.streamlit` directory in your project's root if it doesn't exist.
    *   Inside `.streamlit`, create a file named `secrets.toml` and add your API key in the format `GOOGLE_API_KEY="your-google-api-key-here"`.
    *   Be sure to not upload your API key if using github, add this to the `.gitignore` file

5.  **Place Schema Files:**
    Ensure your competency framework JSON files are located in the `Schemas/` directory. Example files (`cfap_ap.json`, `hcpc_generic.json`, `hcpc_paramedics.json`, `rps_prescribing.json`, etc.) are expected.

### 🏃 How to Run:

With your virtual environment activated, run the Streamlit application using the command: `.venv/bin/python -m streamlit run portfolio_mapper.app.py`. This will open the application in your web browser.

### License:

This is dual licensed, for those in the NHS this is with a MIT license. For commercial use, please contact me.

