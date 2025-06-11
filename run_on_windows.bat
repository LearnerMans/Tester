@echo off
setlocal

REM Configuration
set PYTHON_CMD=python
set VENV_DIR=venv
set REQUIREMENTS_FILE=ai_testing_platform/requirements.txt
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

REM --- Refined Instance Directory Creation Logic ---
REM Ensure ai_testing_platform directory exists (it's the main app folder)
if not exist ai_testing_platform (
    echo ERROR: The main application directory 'ai_testing_platform' was not found.
    echo Please ensure you are running this script from the root of the project directory.
    goto :deactivate_env_and_eof
)

echo Changing current directory to 'ai_testing_platform' to create instance folder...
pushd ai_testing_platform
if errorlevel 1 (
    echo ERROR: Failed to change directory to 'ai_testing_platform'. This should not happen if the above check passed.
    goto :deactivate_env_and_eof
)

echo Checking for 'instance' directory (from within 'ai_testing_platform')...
if not exist instance (
    echo Creating 'instance' directory...
    mkdir instance
    if errorlevel 1 (
        echo ERROR: Failed to create 'instance' directory inside 'ai_testing_platform'.
        echo Please check permissions.
        popd
        goto :deactivate_env_and_eof
    )
    echo 'instance' directory created successfully.
) else (
    echo 'instance' directory already exists.
)

echo Returning to original directory...
popd
echo.
REM --- End of Refined Instance Directory Creation Logic ---

REM Check for config.json
REM Note: CONFIG_FILE path is relative to original script execution dir (project root).
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
