"""Web Interface for JARVIS Agent"""
import os
import sys
from typing import Dict, Any, Optional
from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import JarvisAgent
from core.memory import ConversationMemory


class WebInterface:
    """Web interface handler for JARVIS Agent"""
    
    def __init__(self):
        # Get absolute paths for templates and static files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, "web", "templates")
        static_dir = os.path.join(current_dir, "web", "static")
        
        # Create Jinja2 environment with disabled caching to avoid the error
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        
        self.templates = Jinja2Templates(env=env)
        self.static_files = StaticFiles(directory=static_dir)
        self.active_connections: Dict[str, WebSocket] = {}
    
    def setup_routes(self, app):
        """Setup web interface routes"""
        
        @app.get("/")
        async def chat_interface(request: Request):
            """Serve the chat interface"""
            return self.templates.TemplateResponse("chat.html", {"request": request})
        
        @app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for real-time chat"""
            await self.connect_websocket(websocket, session_id)
            
            try:
                # Import here to avoid circular imports
                from ..server.app import get_agent, get_session_memory
                
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
                    await self.send_message(session_id, {
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
                        await self.send_message(session_id, {
                            "type": "message",
                            "response": response,
                            "session_id": session_id,
                            "timestamp": str(memory.events[-1].timestamp.isoformat()) if memory.events else ""
                        })
                        
                    finally:
                        # Restore original memory
                        agent.memory = original_memory
                        
            except WebSocketDisconnect:
                self.disconnect_websocket(session_id)
            except Exception as e:
                await self.send_message(session_id, {
                    "type": "error",
                    "message": str(e)
                })
                self.disconnect_websocket(session_id)
    
    async def connect_websocket(self, websocket: WebSocket, session_id: str):
        """Connect WebSocket"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect_websocket(self, session_id: str):
        """Disconnect WebSocket"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)
    
    def get_static_files(self):
        """Get static files handler"""
        return self.static_files
    
    def get_templates(self):
        """Get templates handler"""
        return self.templates


# Global web interface instance
web_interface = WebInterface()
