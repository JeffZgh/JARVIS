import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Jarvis Dev Agent",
    instructions="""
    You are a cautious coding assistant.
    For now, do not edit files or run shell commands.
    Only explain what you would do.
    """
)

async def main():
    result = await Runner.run(
        agent,
        "I want to build a Python project. What files should I create first?"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())