"""Base tool class for JARVIS Agent"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class PermissionLevel(Enum):
    """Permission levels for tools"""
    READ = "read"
    WRITE = "write"
    SENSITIVE = "sensitive"
    ADMIN = "admin"


class BaseTool(ABC):
    """Base class for all tools in JARVIS Agent"""
    
    def __init__(self, name: str, description: str, permission_level: PermissionLevel = PermissionLevel.READ):
        self.name = name
        self.description = description
        self.permission_level = permission_level
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.value
        }
    
    def validate_params(self, **kwargs) -> bool:
        """Validate parameters before execution"""
        return True
