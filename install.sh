#!/usr/bin/env bash
# Installation script for AIpp Opener

set -e

echo "==================================="
echo "AIpp Opener - Installation Script"
echo "==================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
echo ""
echo "To use AIpp Opener:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python -m aipp_opener --help"
echo ""
echo "  3. For voice input, ensure you have a microphone connected."
echo ""
echo "  4. For AI features, make sure Ollama is running:"
echo "     ollama serve"
echo ""
echo "     And pull a model:"
echo "     ollama pull llama3.2"
echo ""
