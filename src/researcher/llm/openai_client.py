"""OpenAI and OpenAI-compatible client implementation.

This module provides an LLM client for OpenAI and OpenAI-compatible services.
"""

import json
import os
from typing import Any

from loguru import logger
from openai import AsyncOpenAI

from researcher.core.tool import Tool
from researcher.llm.base import (
    FunctionCall,
    LLMClient,
    LLMResponse,
    Message,
    ToolCall,
)


class OpenAIClient(LLMClient):
    """OpenAI and OpenAI-compatible LLM client.

    Supports:
    - Official OpenAI (GPT-4, GPT-3.5, etc.)
    - OpenAI-compatible services (DeepSeek, Ollama, vLLM, LocalAI, etc.)
    - Tool calling (function calling)

    Environment Variables:
    - OPENAI_API_KEY: API key (optional for local services)
    - OPENAI_BASE_URL: Base URL (default: https://api.openai.com/v1)
    - OPENAI_MODEL: Default model (default: gpt-4o)

    Examples:
        # Official OpenAI
        >>> client = OpenAIClient(api_key="sk-...", model="gpt-4o")

        # DeepSeek
        >>> client = OpenAIClient(
        ...     api_key="sk-...",
        ...     base_url="https://api.deepseek.com/v1",
        ...     model="deepseek-chat"
        ... )

        # Local Ollama
        >>> client = OpenAIClient(
        ...     api_key="",
        ...     base_url="http://localhost:11434/v1",
        ...     model="llama3"
        ... )

        # From environment variables
        >>> # export OPENAI_BASE_URL=https://api.deepseek.com/v1
        >>> # export OPENAI_API_KEY=sk-...
        >>> # export OPENAI_MODEL=deepseek-chat
        >>> client = OpenAIClient()
    """

    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
    ):
        """Initialize OpenAI-compatible client.

        Args:
            api_key: API key. If None, reads from OPENAI_API_KEY.
                    Use empty string "" for services that don't require auth.
            base_url: API base URL. If None, reads from OPENAI_BASE_URL,
                     defaults to "https://api.openai.com/v1"
            model: Model name. If None, reads from OPENAI_MODEL,
                  defaults to "gpt-4o"
            max_tokens: Maximum tokens to generate (default: 8192)

        Raises:
            ValueError: If api_key is not provided and OPENAI_API_KEY is not set
        """
        # Handle API key
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError(
                    "API key required. Set OPENAI_API_KEY environment variable "
                    'or pass api_key parameter. Use api_key="" for services '
                    "that don't require authentication."
                )

        # Handle base URL
        if base_url is None:
            base_url = os.getenv("OPENAI_BASE_URL", self.DEFAULT_BASE_URL)

        # Handle model
        if model is None:
            model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = base_url

        logger.info(f"Initialized OpenAIClient: base_url={base_url}, model={model}")

    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from OpenAI-compatible API.

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
        # Convert messages to OpenAI format (system_prompt unused for OpenAI)
        _, api_messages = self._convert_messages(messages)

        # Build API parameters
        params: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "messages": api_messages,
        }

        # Add tools if provided
        if tools:
            params["tools"] = self._convert_tools(tools)

        # Add optional parameters
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]

        logger.debug(
            f"Calling OpenAI API: model={params['model']}, "
            f"messages={len(api_messages)}, tools={len(tools) if tools else 0}"
        )

        # Make API call
        try:
            response = await self.client.chat.completions.create(**params)
            logger.debug(
                f"OpenAI response: finish_reason={response.choices[0].finish_reason}, "
                f"usage={response.usage.model_dump() if response.usage else None}"
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Parse and return response
        return self._parse_response(response)

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert messages to OpenAI format.

        OpenAI format:
        - system messages are included in the messages list
        - tool results are in tool role messages

        Args:
            messages: Internal message list

        Returns:
            List of messages in OpenAI format
        """
        system_prompt = None
        api_messages = []

        for msg in messages:
            # System messages
            if msg.role == "system":
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                api_messages.append({"role": "system", "content": content})
                continue

            # Tool messages
            if msg.role == "tool":
                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                )
                continue

            # User/Assistant messages
            content = msg.content if isinstance(msg.content, str) else msg.content

            message_dict: dict[str, Any] = {
                "role": msg.role,
                "content": content,
            }

            # Add tool calls if present (assistant messages only)
            if msg.tool_calls:
                message_dict["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    message_dict["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": json.dumps(tool_call.function.arguments),
                            },
                        }
                    )

            api_messages.append(message_dict)

        return system_prompt, api_messages

    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert Tool objects to OpenAI format.

        OpenAI tool format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "Tool description",
                "parameters": { ... JSON Schema ... }
            }
        }

        Args:
            tools: List of Tool objects

        Returns:
            List of tool definitions in OpenAI format
        """
        return [tool.to_openai_schema() for tool in tools]

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse OpenAI response to LLMResponse.

        Args:
            response: Raw response from OpenAI API

        Returns:
            Standardized LLMResponse
        """
        choice = response.choices[0]
        message = choice.message

        # Extract text content
        text_content = self._extract_text_content(message.content)

        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                # Parse arguments (may be string or dict)
                arguments = tc.function.arguments
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse tool arguments: {}", arguments)
                        arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        type="function",
                        function=FunctionCall(name=tc.function.name, arguments=arguments),
                    )
                )

        # Extract usage information
        usage = None
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
            usage=usage,
        )

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text content from OpenAI message content."""
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        parts: list[str] = []
        if isinstance(content, list):
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    if part.get("type") == "text":
                        parts.append(part.get("text", ""))
                else:
                    part_type = getattr(part, "type", None)
                    if part_type == "text":
                        parts.append(getattr(part, "text", ""))
            return "".join(parts)

        # Fallback for unexpected structures
        return str(content)
