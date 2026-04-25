"""FastAPI server for JARVIS Agent"""
import asyncio
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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

# Note: Web interface routes removed to avoid Jinja2 template issues
# The chat interface is now served directly via HTML response


@app.get("/")
async def root():
    """Root endpoint - serve chat interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JARVIS Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .chat-container {
                width: 90%;
                max-width: 800px;
                height: 90vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 1.5em;
                font-weight: bold;
            }
            
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
            }
            
            .message {
                margin-bottom: 15px;
                display: flex;
                align-items: flex-start;
            }
            
            .message.user {
                justify-content: flex-end;
            }
            
            .message.assistant {
                justify-content: flex-start;
            }
            
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
            }
            
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .message.assistant .message-content {
                background: white;
                color: #333;
                border: 1px solid #e9ecef;
                border-bottom-left-radius: 4px;
            }
            
            .message-time {
                font-size: 0.8em;
                color: #666;
                margin-top: 5px;
            }
            
            .chat-input {
                padding: 20px;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 10px;
            }
            
            .input-field {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                border-radius: 25px;
                font-size: 16px;
                outline: none;
                transition: border-color 0.3s;
            }
            
            .input-field:focus {
                border-color: #667eea;
            }
            
            .send-button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .send-button:hover {
                transform: scale(1.05);
            }
            
            .send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: scale(1);
            }
            
            .status-indicator {
                padding: 10px;
                text-align: center;
                font-size: 0.9em;
                color: #666;
                background: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
            }
            
            .status-indicator.connected {
                color: #28a745;
            }
            
            .status-indicator.connecting {
                color: #ffc107;
            }
            
            .status-indicator.error {
                color: #dc3545;
            }
            
            .typing-indicator {
                font-style: italic;
                color: #666;
                padding: 10px 20px;
            }
            
            .clear-button {
                padding: 8px 16px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 12px;
                cursor: pointer;
                margin-left: 10px;
            }
            
            .session-info {
                font-size: 0.8em;
                color: #666;
                margin-left: auto;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                🤖 JARVIS Agent
                <button class="clear-button" onclick="clearHistory()">Clear</button>
                <span class="session-info" id="sessionInfo"></span>
            </div>
            
            <div class="status-indicator" id="statusIndicator">
                Connecting...
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    <div class="message-content">
                        Hello! I'm JARVIS, your AI assistant. How can I help you today?
                    </div>
                </div>
            </div>
            
            <div class="chat-input">
                <input type="text" class="input-field" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            let ws = null;
            let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
            let isConnected = false;
            
            // Initialize session
            document.getElementById('sessionInfo').textContent = 'Session: ' + sessionId;
            
            // Connect WebSocket
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
                
                updateStatus('Connecting...', 'connecting');
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    isConnected = true;
                    updateStatus('Connected', 'connected');
                    document.getElementById('sendButton').disabled = false;
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    isConnected = false;
                    updateStatus('Disconnected', 'error');
                    document.getElementById('sendButton').disabled = true;
                    
                    // Try to reconnect after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    updateStatus('Connection error', 'error');
                };
            }
            
            function handleWebSocketMessage(data) {
                if (data.type === 'message') {
                    addMessage('assistant', data.response);
                } else if (data.type === 'typing') {
                    if (data.status === 'started') {
                        showTypingIndicator();
                    } else {
                        hideTypingIndicator();
                    }
                } else if (data.type === 'error') {
                    addMessage('assistant', 'Error: ' + data.message);
                }
            }
            
            function updateStatus(message, className) {
                const indicator = document.getElementById('statusIndicator');
                indicator.textContent = message;
                indicator.className = 'status-indicator ' + className;
            }
            
            function addMessage(type, content) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = content;
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'message-time';
                timeDiv.textContent = new Date().toLocaleTimeString();
                
                messageDiv.appendChild(contentDiv);
                messageDiv.appendChild(timeDiv);
                messagesContainer.appendChild(messageDiv);
                
                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function showTypingIndicator() {
                hideTypingIndicator();
                const messagesContainer = document.getElementById('chatMessages');
                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing-indicator';
                typingDiv.id = 'typingIndicator';
                typingDiv.textContent = 'JARVIS is typing...';
                messagesContainer.appendChild(typingDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function hideTypingIndicator() {
                const typingIndicator = document.getElementById('typingIndicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && isConnected) {
                    // Add user message to chat
                    addMessage('user', message);
                    
                    // Send via WebSocket
                    ws.send(JSON.stringify({
                        message: message,
                        message_type: 'text'
                    }));
                    
                    // Clear input
                    input.value = '';
                    
                    // Disable send button temporarily
                    document.getElementById('sendButton').disabled = true;
                }
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            }
            
            function clearHistory() {
                if (confirm('Are you sure you want to clear the chat history?')) {
                    const messagesContainer = document.getElementById('chatMessages');
                    messagesContainer.innerHTML = `
                        <div class="message assistant">
                            <div class="message-content">
                                Hello! I'm JARVIS, your AI assistant. How can I help you today?
                            </div>
                        </div>
                    `;
                }
            }
            
            // Initialize connection
            connectWebSocket();
            
            // Fallback to HTTP API if WebSocket fails
            async function sendMessageViaAPI(message) {
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: sessionId
                        })
                    });
                    
                    const data = await response.json();
                    addMessage('assistant', data.response);
                } catch (error) {
                    addMessage('assistant', 'Error: ' + error.message);
                } finally {
                    document.getElementById('sendButton').disabled = false;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        agent = get_agent()
        memory = get_session_memory(session_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            message_type = data.get("message_type", "text")
            
            if not message:
                continue
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "status": "started"
            })
            
            # Temporarily switch agent's memory for this session
            original_memory = agent.memory
            agent.memory = memory
            
            try:
                # Get response from agent
                response = await agent.chat(message, message_type)
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "response": response,
                    "session_id": session_id,
                    "timestamp": str(memory.events[-1].timestamp.isoformat()) if memory.events else ""
                })
                
            finally:
                # Restore original memory
                agent.memory = original_memory
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    
    print("Starting JARVIS Agent Server...")
    print("API will be available at: http://localhost:8000")
    print("WebSocket will be available at: ws://localhost:8000/ws/{session_id}")
    print("API docs at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
