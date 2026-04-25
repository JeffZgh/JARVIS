import asyncio
import os
from agents import Agent, Runner
from typing import Optional, Dict, Any
from .memory import ConversationMemory, UserMessage, AssistantMessage, ToolCall, SystemEvent
from .config import config


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
        
        # Create agent with configurable settings
        self.agent = Agent(
            name=config.agent_name,
            instructions=self._get_instructions(),
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            top_p=config.llm.top_p,
            frequency_penalty=config.llm.frequency_penalty,
            presence_penalty=config.llm.presence_penalty
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
        self.agent = Agent(
            name=config.agent_name,
            instructions=self._get_instructions(),
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            top_p=config.llm.top_p,
            frequency_penalty=config.llm.frequency_penalty,
            presence_penalty=config.llm.presence_penalty
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
    
    async def chat(self, message: str, message_type: str = "text") -> str:
        """Send a message to the agent and get response"""
        try:
            # Add user message to comprehensive memory
            self.memory.add_user_message(content=message, message_type=message_type)
            
            # Build comprehensive context
            conversation_context = self.memory.build_context_string()
            
            # Add system event for processing start
            self.memory.add_system_event(
                event_name="message_processing",
                description=f"Processing user message: {message[:50]}..."
            )
            
            result = await Runner.run(
                self.agent,
                conversation_context + "\n\nCurrent User Message: " + message
            )
            
            response = result.final_output
            
            # Add assistant response to memory
            self.memory.add_assistant_message(content=response)
            
            # Check if any tools were called and add them to memory
            if hasattr(result, 'tool_calls') and result.tool_calls:
                for tool_call in result.tool_calls:
                    self.memory.add_tool_call(
                        tool_name=tool_call.name,
                        tool_args=tool_call.arguments,
                        tool_result=getattr(tool_call, 'result', None),
                        success=getattr(tool_call, 'success', True)
                    )
            
            # Add system event for processing complete
            self.memory.add_system_event(
                event_name="message_processed",
                description="Message processing completed successfully",
                severity="info"
            )
            
            return response
        except Exception as e:
            # Add error event to memory
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
