"""Core abstractions for the Researcher system.

This module provides the foundational base classes and data models:
- Tool: Abstract base class for all tools
- ToolResult: Standardized return value for tool execution
"""

from researcher.core.tool import Tool, ToolResult

__all__ = ["Tool", "ToolResult"]
