#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export PYTHONPATH=$DIR

echo "Setting PYTHONPATH to $PYTHONPATH"

# Check if environment folder exists
if [ ! -d "environment" ]; then
    echo "Creating virtual environment..."
    python3 -m venv environment
fi

# Activate the virtual environment
source environment/bin/activate

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run the Synapse Architect GUI
if [ -f "synapse/gui/main_window.py" ]; then
    echo "Launching Synapse VS Architect..."
    python3 synapse/gui/main_window.py "$@"
else
    echo "Error: synapse/gui/main_window.py not found."
fi
