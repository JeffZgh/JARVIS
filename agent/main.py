#!/usr/bin/env python3
"""
JARVIS Agent - Simple conversational assistant
"""
import asyncio
import sys
import os

# Add the agent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent import JarvisAgent


async def main():
    """Main entry point for JARVIS assistant"""
    try:
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY environment variable is not set")
            print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
            return
        
        # Create and start the agent
        agent = JarvisAgent()
        await agent.start_conversation()
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
