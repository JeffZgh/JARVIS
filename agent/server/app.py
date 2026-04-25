"""FastAPI server for JARVIS Agent"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import JarvisAgent
from core.memory import ConversationMemory
from core.config import config
from interfaces.web_interface import web_interface


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    message_type: str = "text"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    timestamp: str


class LLMSettings(BaseModel):
    """LLM settings model"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    created_at: str
    message_count: int
    memory_stats: Dict[str, int]


# Global agent instance
agent_instance: Optional[JarvisAgent] = None
active_sessions: Dict[str, ConversationMemory] = {}


def get_agent() -> JarvisAgent:
    """Get or create agent instance"""
    global agent_instance
    if agent_instance is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        agent_instance = JarvisAgent()
    return agent_instance


def get_session_memory(session_id: str) -> ConversationMemory:
    """Get or create session memory"""
    if session_id not in active_sessions:
        active_sessions[session_id] = ConversationMemory(session_id=session_id)
    return active_sessions[session_id]


# Create FastAPI app
app = FastAPI(
    title="JARVIS Agent API",
    description="API for JARVIS AI Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from web interface
app.mount("/static", web_interface.get_static_files(), name="static")

# Setup web interface routes
web_interface.setup_routes(app)


@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "message": "JARVIS Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "agent_ready": True,
            "active_sessions": len(active_sessions)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "agent_ready": False
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat endpoint"""
    try:
        agent = get_agent()
        
        # Generate session ID if not provided
        session_id = message.session_id or str(uuid.uuid4())
        memory = get_session_memory(session_id)
        
        # Temporarily switch agent's memory for this session
        original_memory = agent.memory
        agent.memory = memory
        
        try:
            # Get response from agent
            response = await agent.chat(message.message, message.message_type)
            
            return ChatResponse(
                response=response,
                session_id=session_id,
                timestamp=str(memory.events[-1].timestamp.isoformat()) if memory.events else ""
            )
        finally:
            # Restore original memory
            agent.memory = original_memory
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions = []
    for session_id, memory in active_sessions.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            created_at=memory.events[0].timestamp.isoformat() if memory.events else "",
            message_count=len(memory.events),
            memory_stats={
                "total_events": len(memory.events),
                "user_messages": len(memory.get_events_by_type("user_message")),
                "assistant_messages": len(memory.get_events_by_type("assistant_message")),
                "tool_calls": len(memory.get_events_by_type("tool_call"))
            }
        ))
    return {"sessions": sessions}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    memory = active_sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": memory.events[0].timestamp.isoformat() if memory.events else "",
        "context": memory.build_context_string(),
        "memory_stats": {
            "total_events": len(memory.events),
            "user_messages": len(memory.get_events_by_type("user_message")),
            "assistant_messages": len(memory.get_events_by_type("assistant_message")),
            "tool_calls": len(memory.get_events_by_type("tool_call")),
            "system_events": len(memory.get_events_by_type("system_event"))
        }
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    return {"message": "Session deleted"}


@app.get("/config/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    try:
        agent = get_agent()
        return agent.get_current_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLM config: {str(e)}")


@app.put("/config/llm")
async def update_llm_config(settings: LLMSettings):
    """Update LLM configuration"""
    try:
        agent = get_agent()
        agent.update_llm_settings(
            model=settings.model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            presence_penalty=settings.presence_penalty
        )
        return {"message": "LLM configuration updated", "settings": agent.get_current_settings()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update LLM config: {str(e)}")


@app.get("/config")
async def get_full_config():
    """Get full configuration (excluding sensitive data)"""
    try:
        config.validate()
        return {
            "agent_name": config.agent_name,
            "llm": config.get_llm_config().to_dict(),
            "memory": {
                "max_conversation_history": config.max_conversation_history,
                "context_window_size": config.context_window_size
            },
            "safety": {
                "enable_guardrails": config.enable_guardrails,
                "default_permission_level": config.default_permission_level
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("Starting JARVIS Agent Server...")
    print("API will be available at: http://localhost:8000")
    print("WebSocket will be available at: ws://localhost:8000/ws/{session_id}")
    print("API docs at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
