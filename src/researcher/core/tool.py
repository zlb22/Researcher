"""Tool base classes and result models for the Researcher system.

This module provides the foundational abstractions for all tools in the system:
- ToolResult: Standardized return value for tool execution
- Tool: Abstract base class that all tools must inherit from
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolResult(BaseModel):
    """Standardized result returned by tool execution.

    Attributes:
        success: Whether the tool execution succeeded
        content: Brief summary of the result (should be concise, < 500 tokens for agent tools)
        error: Error message if execution failed (None if successful)
        metadata: Additional structured data (e.g., file paths, statistics, full output)

    Examples:
        >>> # Successful execution
        >>> ToolResult(
        ...     success=True,
        ...     content="File read successfully. Contains 150 lines.",
        ...     metadata={"filepath": "workspace/data.txt", "line_count": 150}
        ... )

        >>> # Failed execution
        >>> ToolResult(
        ...     success=False,
        ...     content="",
        ...     error="File not found: workspace/missing.txt"
        ... )
    """

    success: bool = Field(description="Whether the tool execution succeeded")
    content: str = Field(default="", description="Result content (brief summary)")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (e.g., file paths, stats)"
    )

    # Pydantic v2 configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Tool(ABC):
    """Abstract base class for all tools in the Researcher system.

    All tools must implement:
    - name: Unique tool identifier
    - description: Clear description of what the tool does
    - parameters: JSON Schema defining the tool's parameters
    - execute: Async method that performs the tool's action

    Tools can be converted to different LLM provider formats:
    - to_schema(): Anthropic format
    - to_openai_schema(): OpenAI format

    Example:
        >>> class MyTool(Tool):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_tool"
        ...
        ...     @property
        ...     def description(self) -> str:
        ...         return "Does something useful"
        ...
        ...     @property
        ...     def parameters(self) -> dict[str, Any]:
        ...         return {
        ...             "type": "object",
        ...             "properties": {
        ...                 "input": {"type": "string", "description": "Input text"}
        ...             },
        ...             "required": ["input"]
        ...         }
        ...
        ...     async def execute(self, input: str) -> ToolResult:
        ...         return ToolResult(success=True, content=f"Processed: {input}")
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool.

        Should be lowercase with underscores (e.g., 'read_file', 'web_search').
        This name will be used by the LLM to invoke the tool.

        Returns:
            Tool name string
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does.

        This description helps the LLM understand when to use the tool.
        Should be clear, concise, and action-oriented.

        Returns:
            Tool description string
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema defining the tool's parameters.

        Must follow JSON Schema specification (https://json-schema.org/).
        The schema should define:
        - type: Usually "object"
        - properties: Dict of parameter definitions
        - required: List of required parameter names

        Returns:
            JSON Schema dict

        Example:
            {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number (optional)"
                    }
                },
                "required": ["filepath"]
            }
        """
        raise NotImplementedError

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given arguments.

        This method performs the actual work of the tool. It should:
        1. Validate inputs (though LLM should provide valid args per schema)
        2. Perform the tool's operation
        3. Return a ToolResult with success/failure status
        4. Catch exceptions and convert to ToolResult(success=False, error=...)

        Args:
            **kwargs: Tool parameters as defined in the parameters schema

        Returns:
            ToolResult indicating success/failure and containing result data

        Note:
            - This method MUST be async
            - Exceptions should be caught and returned as failed ToolResult
            - For agent tools, keep content brief (< 500 tokens), put details in metadata
        """
        raise NotImplementedError

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to Anthropic tool schema format.

        Anthropic expects tools in this format:
        {
            "name": "tool_name",
            "description": "Tool description",
            "input_schema": { ... JSON Schema ... }
        }

        Returns:
            Dict in Anthropic tool format
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI tool schema format.

        OpenAI expects tools in this format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "Tool description",
                "parameters": { ... JSON Schema ... }
            }
        }

        Returns:
            Dict in OpenAI tool format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
