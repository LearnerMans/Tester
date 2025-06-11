@echo off
setlocal

REM Configuration
set PYTHON_CMD=python
set VENV_DIR=venv
set REQUIREMENTS_FILE=ai_testing_platform/requirements.txt
REM CONFIG_FILE uses forward slashes as it's used by Python later, which is fine.
set CONFIG_FILE=ai_testing_platform/instance/config.json
set APP_SCRIPT=ai_testing_platform/run.py

echo ================================================
echo AI Agent Testing Platform - Windows Setup & Run
echo ================================================
echo.

REM Check for Python
echo Checking for Python installation...
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found or not in PATH. Please install Python 3.7+ and ensure it's added to your PATH.
    goto :eof
)
echo Python found.
echo.

REM Check/Create Virtual Environment
if not exist %VENV_DIR%\Scripts\activate.bat (
    echo Creating virtual environment in '%VENV_DIR%'...
    %PYTHON_CMD% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        goto :eof
    )
    echo Virtual environment created.
) else (
    echo Virtual environment found.
)
echo.

REM Activate Virtual Environment and Install Dependencies
echo Activating virtual environment and installing dependencies...
call %VENV_DIR%\Scripts\activate.bat

echo Installing dependencies from %REQUIREMENTS_FILE%...
pip install -r %REQUIREMENTS_FILE%
if errorlevel 1 (
    echo ERROR: Failed to install dependencies. Please check your internet connection and '%REQUIREMENTS_FILE%'.
    goto :deactivate_env_and_eof
)
echo Dependencies installed successfully.
echo.

REM Ensure ai_testing_platform directory exists (it's the main app folder)
if not exist ai_testing_platform (
    echo ERROR: The main application directory 'ai_testing_platform' was not found.
    echo Please ensure you are running this script from the root of the project directory.
    goto :deactivate_env_and_eof
)

REM Define and create the instance directory using Windows-style backslashes
set INSTANCE_DIR_WIN=ai_testing_platform\instance

echo Checking for instance directory: %INSTANCE_DIR_WIN%
if not exist %INSTANCE_DIR_WIN% (
    echo Creating instance directory: %INSTANCE_DIR_WIN%
    mkdir %INSTANCE_DIR_WIN%
    if errorlevel 1 (
        echo ERROR: Failed to create instance directory (%INSTANCE_DIR_WIN%).
        echo Please check permissions and path.
        goto :deactivate_env_and_eof
    )
    echo Instance directory created.
) else (
    echo Instance directory already exists.
)
echo.

REM Check for config.json
echo Checking for configuration file: %CONFIG_FILE%
if not exist %CONFIG_FILE% (
    echo.
    echo WARNING: Configuration file (%CONFIG_FILE%) not found!
    echo Please create this file with the following structure:
    echo {
    echo     "api_key": "sk-YOUR_OPENAI_API_KEY",
    echo     "api_endpoint": ""
    echo }
    echo Replace sk-YOUR_OPENAI_API_KEY with your actual OpenAI API key.
    echo The 'api_endpoint' can be left empty or set to a custom OpenAI-compatible base URL.
    echo.
    pause
    if not exist %CONFIG_FILE% (
        echo ERROR: Configuration file still not found. Exiting.
        goto :deactivate_env_and_eof
    )
)
echo Configuration file found.
echo.

REM Run the application
echo Starting the Flask application (%APP_SCRIPT%)...
echo Navigate to http://127.0.0.1:5000/ in your web browser once the server starts.
%PYTHON_CMD% %APP_SCRIPT%
if errorlevel 1 (
    echo ERROR: Failed to run the application.
)

:deactivate_env_and_eof
echo Deactivating virtual environment (if active from this script context)...
endlocal
echo.
echo Script finished.
pause
goto :eof

:eof
endlocal
echo.
echo Script aborted due to error.
pause
