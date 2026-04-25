#!/usr/bin/env python3
"""
JARVIS Agent Server - Main entry point
"""
import os
import sys
import asyncio

# Add the agent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.app import app

def main():
    """Main entry point for the server"""
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set")
        print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("Starting JARVIS Agent Server...")
    print("API will be available at: http://localhost:8000")
    print("WebSocket will be available at: ws://localhost:8000/ws/{session_id}")
    print("API docs at: http://localhost:8000/docs")
    
    # Import uvicorn here to avoid import issues
    import uvicorn
    
    # Run the server
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
