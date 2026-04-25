"""Comprehensive conversation memory system for JARVIS Agent"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ConversationEvent:
    """Base class for all conversation events"""
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default="")
    event_type: str = field(default="")
    session_id: str = field(default="default")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id
        }


@dataclass
class UserMessage(ConversationEvent):
    """User input message"""
    content: str = field(default="")
    message_type: str = field(default="text")  # text, voice, file_upload
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = "user_message"
        if not self.event_id:
            self.event_id = f"user_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class AssistantMessage(ConversationEvent):
    """Assistant response message"""
    content: str = field(default="")
    message_type: str = field(default="text")  # text, voice, file
    confidence: float = field(default=1.0)
    reasoning: Optional[str] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = "assistant_message"
        if not self.event_id:
            self.event_id = f"assistant_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class ToolCall(ConversationEvent):
    """Tool invocation event"""
    tool_name: str = field(default="")
    tool_args: Dict[str, Any] = field(default_factory=dict)
    tool_result: Any = field(default=None)
    execution_time: float = field(default=0.0)
    success: bool = field(default=True)
    error_message: Optional[str] = field(default=None)
    
    def __post_init__(self):
        self.event_type = "tool_call"
        if not self.event_id:
            self.event_id = f"tool_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class SystemEvent(ConversationEvent):
    """System-level events"""
    event_name: str = field(default="")
    description: str = field(default="")
    severity: str = field(default="info")  # info, warning, error
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = "system_event"
        if not self.event_id:
            self.event_id = f"system_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class ContextUpdate(ConversationEvent):
    """Context/memory updates"""
    context_type: str = field(default="")  # user_preference, project_info, etc.
    key: str = field(default="")
    value: Any = field(default=None)
    operation: str = field(default="set")  # set, delete, update
    
    def __post_init__(self):
        self.event_type = "context_update"
        if not self.event_id:
            self.event_id = f"context_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class SkillExecution(ConversationEvent):
    """High-level skill execution"""
    skill_name: str = field(default="")
    skill_parameters: Dict[str, Any] = field(default_factory=dict)
    skill_result: Any = field(default=None)
    sub_tasks: List[str] = field(default_factory=list)
    success: bool = field(default=True)
    
    def __post_init__(self):
        self.event_type = "skill_execution"
        if not self.event_id:
            self.event_id = f"skill_{int(self.timestamp.timestamp() * 1000)}"


@dataclass
class InterfaceEvent(ConversationEvent):
    """Interface-specific events"""
    interface_type: str = field(default="")  # web, voice, api
    event_name: str = field(default="")
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = "interface_event"
        if not self.event_id:
            self.event_id = f"interface_{int(self.timestamp.timestamp() * 1000)}"


class ConversationMemory:
    """Comprehensive conversation memory management"""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.events: List[ConversationEvent] = []
        self.context: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        self.project_context: Dict[str, Any] = {}
    
    def add_event(self, event: ConversationEvent):
        """Add an event to the conversation history"""
        event.session_id = self.session_id
        self.events.append(event)
        
        # Auto-trim if too many events (keep last 100)
        if len(self.events) > 100:
            self.events = self.events[-100:]
    
    def add_user_message(self, content: str, message_type: str = "text", **metadata):
        """Add user message"""
        event = UserMessage(content=content, message_type=message_type, metadata=metadata)
        self.add_event(event)
        return event
    
    def add_assistant_message(self, content: str, **kwargs):
        """Add assistant message"""
        event = AssistantMessage(content=content, **kwargs)
        self.add_event(event)
        return event
    
    def add_tool_call(self, tool_name: str, tool_args: Dict[str, Any], 
                      tool_result: Any = None, **kwargs):
        """Add tool call event"""
        event = ToolCall(tool_name=tool_name, tool_args=tool_args, tool_result=tool_result, **kwargs)
        self.add_event(event)
        return event
    
    def add_system_event(self, event_name: str, description: str, **kwargs):
        """Add system event"""
        event = SystemEvent(event_name=event_name, description=description, **kwargs)
        self.add_event(event)
        return event
    
    def add_context_update(self, context_type: str, key: str, value: Any, **kwargs):
        """Add context update"""
        event = ContextUpdate(context_type=context_type, key=key, value=value, **kwargs)
        self.add_event(event)
        
        # Update the actual context
        if context_type == "user_preference":
            self.user_preferences[key] = value
        elif context_type == "project_info":
            self.project_context[key] = value
        else:
            self.context[key] = value
        
        return event
    
    def build_context_string(self, max_events: int = 20) -> str:
        """Build comprehensive context string for AI"""
        if not self.events:
            return "This is the beginning of our conversation."
        
        context_parts = []
        recent_events = self.events[-max_events:]
        
        for event in recent_events:
            if isinstance(event, UserMessage):
                context_parts.append(f"User ({event.message_type}): {event.content}")
            elif isinstance(event, AssistantMessage):
                context_parts.append(f"Assistant: {event.content}")
                if event.reasoning:
                    context_parts.append(f"Assistant Reasoning: {event.reasoning}")
            elif isinstance(event, ToolCall):
                status = "Success" if event.success else "Failed"
                context_parts.append(f"Tool Call ({event.tool_name}): {json.dumps(event.tool_args)} - {status}")
                if event.tool_result:
                    context_parts.append(f"Tool Result: {str(event.tool_result)}")
            elif isinstance(event, SystemEvent):
                context_parts.append(f"System [{event.severity}]: {event.description}")
            elif isinstance(event, ContextUpdate):
                context_parts.append(f"Context Update ({event.context_type}): {event.key} = {event.value}")
            elif isinstance(event, SkillExecution):
                status = "Success" if event.success else "Failed"
                context_parts.append(f"Skill ({event.skill_name}): {status}")
        
        # Add current context summary
        if self.context or self.user_preferences or self.project_context:
            context_parts.append("\nCurrent Context:")
            if self.user_preferences:
                context_parts.append(f"User Preferences: {json.dumps(self.user_preferences)}")
            if self.project_context:
                context_parts.append(f"Project Context: {json.dumps(self.project_context)}")
            if self.context:
                context_parts.append(f"General Context: {json.dumps(self.context)}")
        
        return "Conversation History:\n" + "\n".join(context_parts)
    
    def get_events_by_type(self, event_type: str) -> List[ConversationEvent]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_recent_events(self, count: int = 10) -> List[ConversationEvent]:
        """Get most recent events"""
        return self.events[-count:]
    
    def clear_history(self):
        """Clear all conversation history"""
        self.events = []
        self.context = {}
        self.user_preferences = {}
        self.project_context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire memory to dictionary for persistence"""
        return {
            "session_id": self.session_id,
            "events": [event.to_dict() for event in self.events],
            "context": self.context,
            "user_preferences": self.user_preferences,
            "project_context": self.project_context
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore memory from dictionary"""
        self.session_id = data.get("session_id", "default")
        self.context = data.get("context", {})
        self.user_preferences = data.get("user_preferences", {})
        self.project_context = data.get("project_context", {})
        # Note: Event reconstruction would need more complex logic
