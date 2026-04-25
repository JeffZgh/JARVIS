"""Chat-related API routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.agent import JarvisAgent
from core.memory import ConversationMemory
from ..app import get_session_memory, ChatMessage, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message to the agent"""
    try:
        from ..app import get_agent
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


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    try:
        from ..app import active_sessions
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        memory = active_sessions[session_id]
        events = memory.get_recent_events(limit)
        
        history = []
        for event in events:
            history.append({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "content": getattr(event, 'content', None),
                "data": event.to_dict()
            })
        
        return {"session_id": session_id, "history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        from ..app import active_sessions
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        memory = active_sessions[session_id]
        memory.clear_history()
        
        return {"message": "Chat history cleared", "session_id": session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")
