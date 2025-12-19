"""Anthropic Claude client implementation.

This module provides an LLM client for Anthropic's Claude models.
"""

from typing import Any

from anthropic import AsyncAnthropic
from loguru import logger

from researcher.core.tool import Tool
from researcher.llm.base import (
    FunctionCall,
    LLMClient,
    LLMResponse,
    Message,
    ToolCall,
)


class AnthropicClient(LLMClient):
    """LLM client for Anthropic Claude.

    Supports:
    - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
    - Tool calling (function calling)
    - Streaming (future)

    Example:
        >>> client = AnthropicClient(api_key="sk-ant-...")
        >>> response = await client.generate(
        ...     messages=[Message(role="user", content="Hello")],
        ...     model="claude-3-5-sonnet-20241022"
        ... )
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 8192,
    ):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-3-5-sonnet-20241022)
            max_tokens: Maximum tokens to generate (default: 8192)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

        logger.info(f"Initialized AnthropicClient with model: {model}")

    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from Claude.

        Args:
            messages: Conversation history
            tools: Available tools (optional)
            **kwargs: Additional options:
                - model: Override default model
                - max_tokens: Override default max_tokens
                - temperature: Sampling temperature (0-1)

        Returns:
            LLMResponse with content and/or tool calls

        Raises:
            Exception: If API call fails
        """
        # Convert messages to Anthropic format
        system_prompt, api_messages = self._convert_messages(messages)

        # Build API parameters
        params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "messages": api_messages,
        }

        # Add system prompt if present
        if system_prompt:
            params["system"] = system_prompt

        # Add tools if provided
        if tools:
            params["tools"] = self._convert_tools(tools)

        # Add optional parameters
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]

        logger.debug(
            f"Calling Anthropic API: model={params['model']}, "
            f"messages={len(api_messages)}, tools={len(tools) if tools else 0}"
        )

        # Make API call
        try:
            response = await self.client.messages.create(**params)
            logger.debug(
                f"Anthropic response: stop_reason={response.stop_reason}, "
                f"usage={response.usage.model_dump() if response.usage else None}"
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

        # Parse and return response
        return self._parse_response(response)

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert messages to Anthropic format.

        Anthropic requires:
        - system is a separate parameter (not in messages)
        - messages must alternate user/assistant
        - tool results are in user messages as tool_result content blocks

        Args:
            messages: Internal message list

        Returns:
            Tuple of (system_prompt, api_messages)
        """
        system_prompt = None
        api_messages = []

        for msg in messages:
            # Extract system message
            if msg.role == "system":
                system_prompt = msg.content if isinstance(msg.content, str) else str(msg.content)
                continue

            # Convert tool messages to user messages with tool_result blocks
            if msg.role == "tool":
                api_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
                continue

            # Convert user/assistant messages
            content = msg.content if isinstance(msg.content, str) else msg.content

            message_dict: dict[str, Any] = {
                "role": msg.role,
                "content": content,
            }

            # Add tool calls if present (assistant messages only)
            if msg.tool_calls:
                # Convert content to list format for tool calls
                message_dict["content"] = []

                # Add text content if present
                if content:
                    message_dict["content"].append({"type": "text", "text": content})

                # Add tool use blocks
                for tool_call in msg.tool_calls:
                    message_dict["content"].append(
                        {
                            "type": "tool_use",
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "input": tool_call.function.arguments,
                        }
                    )

            api_messages.append(message_dict)

        return system_prompt, api_messages

    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert Tool objects to Anthropic format.

        Anthropic tool format:
        {
            "name": "tool_name",
            "description": "Tool description",
            "input_schema": { ... JSON Schema ... }
        }

        Args:
            tools: List of Tool objects

        Returns:
            List of tool definitions in Anthropic format
        """
        return [tool.to_schema() for tool in tools]

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Anthropic response to LLMResponse.

        Args:
            response: Raw response from Anthropic API

        Returns:
            Standardized LLMResponse
        """
        # Extract text content
        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                # Convert to ToolCall format
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        type="function",
                        function=FunctionCall(name=block.name, arguments=block.input),
                    )
                )

        # Extract usage information
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            usage=usage,
        )
