"""LLM client abstractions for the Researcher system.

This module provides the foundational abstractions for interacting with LLMs:
- Message: Chat message data model
- ToolCall/FunctionCall: Tool calling data models
- LLMResponse: Standardized LLM response
- LLMClient: Abstract base class for LLM providers
"""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from researcher.core.tool import Tool


class FunctionCall(BaseModel):
    """Represents a function call within a tool call.

    Attributes:
        name: Function name (matches Tool.name)
        arguments: Function arguments as a dict
    """

    name: str = Field(description="Function name")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Function arguments")


class ToolCall(BaseModel):
    """Represents a tool call from the LLM.

    Attributes:
        id: Unique identifier for this tool call
        type: Type of call (always "function" for now)
        function: The function call details
    """

    id: str = Field(description="Unique tool call ID")
    type: Literal["function"] = Field(default="function", description="Type of call")
    function: FunctionCall = Field(description="Function call details")


class Message(BaseModel):
    """Represents a chat message.

    Attributes:
        role: Message role (user, assistant, tool)
        content: Message content (text or structured)
        tool_calls: Tool calls made by the assistant (optional)
        tool_call_id: ID of the tool call this message responds to (for tool role)
        name: Tool name (for tool role messages)
    """

    role: Literal["user", "assistant", "tool", "system"] = Field(description="Message role")
    content: str | list[dict] = Field(description="Message content")
    tool_calls: list[ToolCall] | None = Field(default=None, description="Tool calls from assistant")
    tool_call_id: str | None = Field(default=None, description="Tool call ID for tool messages")
    name: str | None = Field(default=None, description="Tool name for tool messages")


class LLMResponse(BaseModel):
    """Standardized response from LLM.

    Attributes:
        content: Text content from the assistant
        tool_calls: Tool calls requested by the assistant
        stop_reason: Why the generation stopped
        usage: Token usage information
    """

    content: str = Field(default="", description="Assistant's text response")
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Tool calls from assistant"
    )
    stop_reason: str | None = Field(default=None, description="Why generation stopped")
    usage: dict[str, int] | None = Field(default=None, description="Token usage stats")


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    All LLM clients (Anthropic, OpenAI, etc.) must implement this interface.
    This allows the Agent to work with any LLM provider seamlessly.

    Example:
        >>> client = AnthropicClient(api_key="...")
        >>> response = await client.generate(
        ...     messages=[Message(role="user", content="Hello")],
        ...     tools=[my_tool]
        ... )
        >>> print(response.content)
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: Conversation history
            tools: Available tools (optional)
            **kwargs: Provider-specific options (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with content and/or tool calls

        Raises:
            Exception: If API call fails
        """
        raise NotImplementedError

    @abstractmethod
    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert internal Message format to provider-specific format.

        Args:
            messages: Internal message list

        Returns:
            Tuple of (system_prompt, api_messages)
            - system_prompt: Extracted system message content (if any)
            - api_messages: Messages in provider's format

        Note:
            - Anthropic: system is a separate parameter
            - OpenAI: system is a message in the list
        """
        raise NotImplementedError

    @abstractmethod
    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert Tool objects to provider-specific format.

        Args:
            tools: List of Tool objects

        Returns:
            List of tool definitions in provider's format

        Note:
            - Anthropic: uses to_schema()
            - OpenAI: uses to_openai_schema()
        """
        raise NotImplementedError

    @abstractmethod
    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse provider-specific response to LLMResponse.

        Args:
            response: Raw response from provider's API

        Returns:
            Standardized LLMResponse
        """
        raise NotImplementedError
