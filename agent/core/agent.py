import asyncio
import os
from agents import Agent, Runner
from typing import Optional, Dict, Any
from .memory import ConversationMemory, UserMessage, AssistantMessage, ToolCall, SystemEvent
from .config import config
from ..tools.tool_registry import tool_registry


class JarvisAgent:
    """Main JARVIS Assistant Agent"""
    
    def __init__(self, session_id: str = "default", llm_config: Optional[Dict[str, Any]] = None):
        # Validate configuration
        config.validate()
        
        # Use comprehensive memory system
        self.memory = ConversationMemory(session_id=session_id)
        
        # Override LLM config if provided
        if llm_config:
            config.update_llm_config(**llm_config)
        
        # Create agent with basic settings
        # Note: LLM parameters are handled through the Runner, not Agent constructor
        self.agent = Agent(
            name=config.agent_name,
            instructions=self._get_instructions()
        )
    
    def _get_instructions(self) -> str:
        """Get agent instructions based on configuration"""
        base_instructions = """
        You are JARVIS, a helpful AI assistant. You are:
        - Friendly and conversational
        - Knowledgeable and helpful
        - Able to assist with various tasks
        - Clear and concise in your responses
        - You maintain context from previous messages in the conversation
        
        You have access to tools that can help you provide more useful information:
        - google_nest: Read room temperature from Google Nest thermostat
        
        When users ask about room temperature, weather, or thermostat information, use the google_nest tool to get current data.
        
        Help users with their questions and tasks to the best of your ability.
        """
        
        # Add temperature-specific instructions
        if config.llm.temperature < 0.3:
            base_instructions += "\n\nYou should be very precise, factual, and analytical in your responses."
        elif config.llm.temperature > 1.0:
            base_instructions += "\n\nYou should be creative, expressive, and explore different possibilities in your responses."
        
        return base_instructions
    
    def update_llm_settings(self, **kwargs) -> None:
        """Update LLM settings dynamically"""
        config.update_llm_config(**kwargs)
        
        # Recreate agent with new settings
        # Note: LLM parameters are handled through the Runner, not Agent constructor
        self.agent = Agent(
            name=config.agent_name,
            instructions=self._get_instructions()
        )
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current LLM settings"""
        return {
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens,
            "top_p": config.llm.top_p,
            "frequency_penalty": config.llm.frequency_penalty,
            "presence_penalty": config.llm.presence_penalty,
            "timeout": config.llm.timeout
        }
    
    async def execute_tool_if_needed(self, message: str) -> Optional[str]:
        """Execute tools if the message requires it"""
        message_lower = message.lower()
        
        # Check if user is asking about temperature
        if any(keyword in message_lower for keyword in [
            "temperature", "temp", "thermostat", "room temperature", 
            "how hot", "how cold", "what's the temperature", "nest"
        ]):
            try:
                result = await tool_registry.execute_tool("google_nest")
                if result["success"]:
                    # Get the temperature summary for all thermostats
                    nest_tool = tool_registry.get_tool("google_nest")
                    if nest_tool:
                        summary = await nest_tool.get_temperature_summary()
                        return summary
                else:
                    return None
            except Exception:
                return None
        
        return None
    
    async def chat(self, message: str, message_type: str = "text") -> str:
        """Send a message to the agent and get response"""
        try:
            self.memory.add_user_message(content=message, message_type=message_type)
            
            # Check if we need to execute any tools
            tool_result = await self.execute_tool_if_needed(message)
            
            # Build comprehensive context
            conversation_context = self.memory.build_context_string()
            
            # Add tool result to context if available
            if tool_result:
                tool_context = f"\n\nCurrent room temperature: {tool_result}°F"
            else:
                tool_context = ""
            
            # Create full prompt with context and tool results
            full_prompt = f"{conversation_context}{tool_context}\n\nUser: {message}\nAssistant: "
            
            # Use simple Runner without LLM parameters for now
            # The OpenAI Agents SDK handles LLM configuration differently
            result = await Runner.run(self.agent, input=full_prompt)
            
            # Extract response - handle RunResult object properly
            if hasattr(result, 'output'):
                response = result.output
            elif hasattr(result, 'final_output'):
                response = result.final_output
            elif hasattr(result, 'result'):
                response = result.result
            else:
                # If it's a RunResult object, extract the actual text
                response_str = str(result)
                if "Final output (str):" in response_str:
                    # Extract the actual response from RunResult string
                    start = response_str.find("Final output (str):") + len("Final output (str):")
                    end = response_str.find("\n", start)
                    if end == -1:
                        end = len(response_str)
                    response = response_str[start:end].strip()
                else:
                    response = response_str
            
            # Add assistant response to memory
            self.memory.add_assistant_message(content=response)
            
            # Check if result contains tool calls and add them to memory
            if hasattr(result, 'tool_calls') and result.tool_calls:
                for tool_call in result.tool_calls:
                    self.memory.add_tool_call(
                        tool_name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        result=str(result.tool_results.get(tool_call.id, "No result"))
                    )
            
            return response
            
        except Exception as e:
            # Add system event to memory
            self.memory.add_system_event(
                event_name="message_processing_error",
                description=f"Error processing message: {str(e)}",
                severity="error"
            )
            return f"Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.memory.clear_history()
    
    def get_memory_stats(self) -> dict:
        """Get statistics about the conversation memory"""
        return {
            "total_events": len(self.memory.events),
            "user_messages": len(self.memory.get_events_by_type("user_message")),
            "assistant_messages": len(self.memory.get_events_by_type("assistant_message")),
            "tool_calls": len(self.memory.get_events_by_type("tool_call")),
            "system_events": len(self.memory.get_events_by_type("system_event")),
            "context_items": len(self.memory.context),
            "user_preferences": len(self.memory.user_preferences),
            "project_context": len(self.memory.project_context)
        }
    
    async def start_conversation(self):
        """Start an interactive conversation"""
        print("JARVIS: Hello! I'm your assistant. How can I help you today?")
        print("Type 'quit' or 'exit' to end the conversation.")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("JARVIS: Goodbye! Have a great day!")
                    break
                
                if not user_input:
                    continue
                
                response = await self.chat(user_input)
                print(f"\nJARVIS: {response}")
                
            except KeyboardInterrupt:
                print("\nJARVIS: Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"\nJARVIS: Sorry, I encountered an error: {str(e)}")


async def main():
    """Main function to run the agent"""
    try:
        agent = JarvisAgent()
        await agent.start_conversation()
    except Exception as e:
        print(f"Failed to start agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
