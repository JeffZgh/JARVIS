#!/bin/bash

# JARVIS Agent Setup Script
# This script sets up the environment and runs the configuration setup

set -e

echo "🤖 JARVIS Agent Setup Script"
echo "============================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

echo "✅ Python 3 and pip3 are installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing requirements..."
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Run configuration setup
echo "⚙️  Running configuration setup..."
python3 setup_config.py

echo ""
echo "🎉 Setup completed!"
echo ""
echo "To start the JARVIS agent:"
echo "  source venv/bin/activate"
echo "  python3 server_main.py"
echo ""
echo "Or run the quick start script:"
echo "  ./start.sh"
