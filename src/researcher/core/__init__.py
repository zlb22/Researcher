"""Core abstractions for the Researcher system.

This module provides the foundational base classes and data models:
- Tool: Abstract base class for all tools
- ToolResult: Standardized return value for tool execution
- WorkspaceManager: Workspace directory management
"""

from researcher.core.tool import Tool, ToolResult
from researcher.core.workspace import WorkspaceManager

__all__ = ["Tool", "ToolResult", "WorkspaceManager"]
