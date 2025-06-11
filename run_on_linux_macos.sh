#!/bin/bash

# Configuration
PYTHON_CMD="python3" # Or python, depending on system setup
VENV_DIR="venv"
REQUIREMENTS_FILE="ai_testing_platform/requirements.txt"
INSTANCE_DIR="ai_testing_platform/instance"
CONFIG_FILE="ai_testing_platform/instance/config.json"
APP_SCRIPT="ai_testing_platform/run.py"

echo "==================================================="
echo "AI Agent Testing Platform - Linux/macOS Setup & Run"
echo "==================================================="
echo

# Check for Python
echo "Checking for Python installation..."
if ! command -v $PYTHON_CMD &> /dev/null
then
    echo "ERROR: $PYTHON_CMD command not found. Please install Python 3.7+."
    exit 1
fi
echo "Python found."
echo

# Check/Create Virtual Environment
if [ ! -d "$VENV_DIR/bin" ]; then
    echo "Creating virtual environment in '$VENV_DIR'..."
    $PYTHON_CMD -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created."
else
    echo "Virtual environment found."
fi
echo

# Activate Virtual Environment and Install Dependencies
echo "Activating virtual environment and installing dependencies..."
source $VENV_DIR/bin/activate

echo "Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r $REQUIREMENTS_FILE
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies. Please check your internet connection and '$REQUIREMENTS_FILE'."
    deactivate # Attempt to deactivate before exiting
    exit 1
fi
echo "Dependencies installed successfully."
echo

# Check/Create Instance Directory
if [ ! -d "$INSTANCE_DIR" ]; then
    echo "Creating instance directory: $INSTANCE_DIR"
    mkdir -p $INSTANCE_DIR # -p creates parent directories if they don't exist
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create instance directory."
        deactivate
        exit 1
    fi
fi
echo

# Check for config.json
echo "Checking for configuration file: $CONFIG_FILE"
if [ ! -f "$CONFIG_FILE" ]; then
    echo
    echo "WARNING: Configuration file ($CONFIG_FILE) not found!"
    echo "Please create this file with the following structure:"
    echo "{"
    echo "    \"api_key\": \"sk-YOUR_OPENAI_API_KEY\","
    echo "    \"api_endpoint\": \"\""
    echo "}"
    echo "Replace sk-YOUR_OPENAI_API_KEY with your actual OpenAI API key."
    echo "The 'api_endpoint' can be left empty or set to a custom OpenAI-compatible base URL."
    echo
    read -p "Press Enter to continue after creating the file..."
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "ERROR: Configuration file still not found. Exiting."
        deactivate
        exit 1
    fi
fi
echo "Configuration file found."
echo

# Run the application
echo "Starting the Flask application ($APP_SCRIPT)..."
echo "Navigate to http://127.0.0.1:5000/ in your web browser once the server starts."
echo "Press Ctrl+C to stop the server."
$PYTHON_CMD $APP_SCRIPT
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to run the application."
fi

echo "Deactivating virtual environment..."
deactivate # Deactivate when script finishes or app is stopped

echo
echo "Script finished."
