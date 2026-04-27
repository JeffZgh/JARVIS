#!/bin/bash

# JARVIS Agent Quick Start Script
# This script activates the virtual environment and starts the JARVIS agent

set -e

echo "🤖 Starting JARVIS Agent..."
echo "=========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Configuration file not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if OpenAI API key is configured
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not found in environment"
    echo "   Make sure your .env file is properly configured"
fi

# Start the server
echo "🚀 Starting JARVIS Agent server..."
echo "   Web interface: http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

python3 server_main.py
