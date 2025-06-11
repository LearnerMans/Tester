# AI Agent Testing Platform

An automated testing platform for conversational AI agents that combines rigid test flows with adaptive AI-driven testing. The system evaluates conversational AI products through structured test cases and provides real-time results through a simple web interface.

## Features Implemented

*   **Test Case Management:**
    *   Upload test cases via Excel files.
    *   Parses Test Case ID, Description, Expected Outcome, and optional Category, Priority, Tags.
    *   Basic validation of Excel format.
    *   Test cases stored in a SQLite database.
    *   Web UI to display and filter test cases.
*   **Conversational AI Integration:**
    *   Configuration page for API endpoint and API key (stored in `instance/config.json`).
    *   Live LLM interaction with OpenAI's GPT-3.5-Turbo (or compatible API).
*   **Test Execution & Evaluation (UI-Driven):**
    *   Users can "run" test cases from the UI.
    *   Supports multi-turn conversations: user can send follow-up messages.
    *   LLM-based evaluation: after a conversation, send it to an LLM for a "Pass/Fail/Inconclusive" verdict and reasoning.
    *   UI pages to display conversation history and evaluation results.
*   **Basic Result Tracking:**
    *   Latest evaluation verdict for each test case shown on the main test list (session-based).
*   **Logging:**
    *   Console logging for test execution turns and evaluation results.

## Setup and Running the Application

You can use the automated scripts or follow the manual setup instructions.

### Automated Setup & Run

**For Windows:**

1.  Open Command Prompt.
2.  Navigate to the root directory of this project.
3.  Run the script: `run_on_windows.bat`
4.  Follow the on-screen prompts. The script will guide you through Python checks, virtual environment setup, dependency installation, and configuration file creation if needed.

**For Linux / macOS:**

1.  Open your terminal.
2.  Navigate to the root directory of this project.
3.  Make the script executable (if not already): `chmod +x run_on_linux_macos.sh`
4.  Run the script: `./run_on_linux_macos.sh`
5.  Follow the on-screen prompts.

### Manual Setup

1.  **Prerequisites:**
    *   Python 3.7+ installed and added to your system's PATH.
    *   `pip` (Python package installer) available.
    *   Git (for cloning the repository, if applicable).

2.  **Clone the Repository (if you haven't already):**
    ```bash
    # git clone <repository_url>
    # cd <repository_directory>
    ```

3.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    ```

4.  **Activate the Virtual Environment:**
    *   **Windows (Command Prompt):**
        ```cmd
        venv\Scripts\activate
        ```
    *   **Windows (PowerShell):**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
        (You might need to set execution policy: `Set-ExecutionPolicy Unrestricted -Scope Process`)
    *   **Linux / macOS (bash/zsh):**
        ```bash
        source venv/bin/activate
        ```

5.  **Install Dependencies:**
    Navigate to the `ai_testing_platform` subdirectory (where `requirements.txt` is located) if your `requirements.txt` is there, or run from root if it's in root. (Assuming `requirements.txt` is in `ai_testing_platform` based on script structure).
    *Adjust path if `requirements.txt` is in the root.*
    ```bash
    pip install -r ai_testing_platform/requirements.txt
    ```
    *(Self-correction: The scripts assume `requirements.txt` is in `ai_testing_platform/`. If it's in the root, this path needs to be `pip install -r requirements.txt` and scripts updated.)*
    *(Correction based on prior steps: `requirements.txt` is in `ai_testing_platform/`)*


6.  **Create Instance Folder and Configuration File:**
    *   Create an `instance` folder inside the `ai_testing_platform` directory:
        ```bash
        # In the root directory of the project:
        mkdir ai_testing_platform/instance
        ```
    *   Inside `ai_testing_platform/instance`, create a file named `config.json`.
    *   Add your OpenAI API key to `config.json`:
        ```json
        {
            "api_key": "sk-YOUR_OPENAI_API_KEY",
            "api_endpoint": ""
        }
        ```
        Replace `sk-YOUR_OPENAI_API_KEY` with your actual key.
        The `api_endpoint` can be left empty to use the default OpenAI URL, or you can specify a custom OpenAI-compatible base URL (e.g., for proxies).

7.  **Initialize the Database:**
    The application should create the SQLite database file automatically on first run if it doesn't exist, based on the SQLAlchemy setup. The database file (`test_cases.db`) will appear in the `ai_testing_platform/instance` folder.

8.  **Run the Application:**
    From the root directory of the project:
    ```bash
    python ai_testing_platform/run.py
    ```

9.  **Access the Application:**
    Open your web browser and navigate to: `http://127.0.0.1:5000/`

## Project Structure

(Brief overview - can be expanded if needed)
- `run.py`: Main script to start the Flask application.
- `ai_testing_platform/`: Main application package.
    - `__init__.py`: Initializes Flask app, database, registers blueprints.
    - `models/`: Contains SQLAlchemy database models (e.g., `test_case.py`).
    - `test_case_management/`: Logic for Excel parsing, etc.
    - `conversation_ai_integration/`: Contains `ai_connector.py` for LLM interactions.
    - `web_interface/`: Flask routes and web-related logic.
    - `static/`: For CSS, JavaScript files (if any).
    - `templates/`: HTML templates.
    - `instance/`: Instance-specific configurations and database file (e.g., `config.json`, `test_cases.db`). This folder is in `.gitignore`.
- `requirements.txt`: Python dependencies (located inside `ai_testing_platform/`). *(Correction: ensure this location is accurate based on project structure. Previous steps put it in `ai_testing_platform/` but often it's in root. For this README, assuming it's in `ai_testing_platform/` as implied by scripts.)*
- `venv/`: Virtual environment directory (should be in `.gitignore`).
- `run_on_windows.bat`: Automated script for Windows.
- `run_on_linux_macos.sh`: Automated script for Linux/macOS.

## Future Development Ideas
(Placeholder for future requirements from the issue document)
- More robust error handling and UI feedback.
- Database storage for all test results, conversation logs, and evaluation history (FR-023, FR-024, FR-026).
- Advanced test case parameters and management.
- Configurable LLM parameters (temperature, model selection for chat vs eval) (FR-016).
- Support for different AI systems beyond a single LLM API.
- Batch test execution (FR-017) and parallel execution (FR-019).
- Test interruption and resumption (FR-021).
- Result export in multiple formats (FR-025).
- Enhanced security for API credentials and data (NFR-009).
