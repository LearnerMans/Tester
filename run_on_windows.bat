@echo off
setlocal

REM Configuration
set PYTHON_CMD=python
set VENV_DIR=venv
set REQUIREMENTS_FILE=ai_testing_platform/requirements.txt
set INSTANCE_DIR=ai_testing_platform/instance
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

REM Check/Create Instance Directory
if not exist %INSTANCE_DIR% (
    echo Creating instance directory: %INSTANCE_DIR%
    mkdir %INSTANCE_DIR%
    if errorlevel 1 (
        echo ERROR: Failed to create instance directory.
        goto :deactivate_env_and_eof
    )
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
REM Deactivation within the same script after 'call' can be tricky.
REM The user might need to manually close the window or it will close on script end.
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
