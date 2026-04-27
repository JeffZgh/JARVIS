"""Tool registry for JARVIS Agent"""
from typing import Dict, List, Any, Optional
from .base_tool import BaseTool, PermissionLevel
from .nest_tool import GoogleNestTool


class ToolRegistry:
    """Registry for managing tools in JARVIS Agent"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        # Register Google Nest tool
        nest_tool = GoogleNestTool()
        self.register_tool(nest_tool)
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def get_tools_by_permission(self, permission_level: PermissionLevel) -> List[BaseTool]:
        """Get tools by permission level"""
        return [tool for tool in self.tools.values() 
                if self._has_permission(tool.permission_level, permission_level)]
    
    def _has_permission(self, tool_permission: PermissionLevel, required_permission: PermissionLevel) -> bool:
        """Check if tool has required permission"""
        permission_hierarchy = {
            PermissionLevel.READ: 0,
            PermissionLevel.WRITE: 1,
            PermissionLevel.SENSITIVE: 2,
            PermissionLevel.ADMIN: 3
        }
        
        return permission_hierarchy[tool_permission] <= permission_hierarchy[required_permission]
    
    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool '{name}': {str(e)}"
            }


# Global tool registry instance
tool_registry = ToolRegistry()
