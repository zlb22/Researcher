"""Tests for the Tool base classes and ToolResult."""

import pytest

from researcher import Tool, ToolResult


class DummyTool(Tool):
    """A simple dummy tool for testing."""

    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "A dummy tool for testing purposes"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input text"},
            },
            "required": ["input"],
        }

    async def execute(self, input: str) -> ToolResult:
        """Execute the dummy tool."""
        return ToolResult(
            success=True,
            content=f"Processed: {input}",
            metadata={"input_length": len(input)},
        )


class TestToolResult:
    """Test ToolResult data model."""

    def test_successful_result(self):
        """Test creating a successful ToolResult."""
        result = ToolResult(success=True, content="Operation completed", metadata={"count": 42})
        assert result.success is True
        assert result.content == "Operation completed"
        assert result.error is None
        assert result.metadata == {"count": 42}

    def test_failed_result(self):
        """Test creating a failed ToolResult."""
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.content == ""
        assert result.error == "Something went wrong"
        assert result.metadata == {}

    def test_result_with_all_fields(self):
        """Test ToolResult with all fields populated."""
        result = ToolResult(
            success=True,
            content="Success message",
            error=None,
            metadata={"key": "value"},
        )
        assert result.success is True
        assert result.content == "Success message"
        assert result.error is None
        assert result.metadata == {"key": "value"}


class TestTool:
    """Test Tool abstract base class."""

    def test_tool_properties(self):
        """Test that tool properties are accessible."""
        tool = DummyTool()
        assert tool.name == "dummy_tool"
        assert tool.description == "A dummy tool for testing purposes"
        assert "properties" in tool.parameters
        assert "input" in tool.parameters["properties"]

    async def test_tool_execute(self):
        """Test tool execution."""
        tool = DummyTool()
        result = await tool.execute(input="hello world")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.content == "Processed: hello world"
        assert result.metadata == {"input_length": 11}

    def test_tool_to_anthropic_schema(self):
        """Test conversion to Anthropic schema format."""
        tool = DummyTool()
        schema = tool.to_schema()

        assert schema["name"] == "dummy_tool"
        assert schema["description"] == "A dummy tool for testing purposes"
        assert "input_schema" in schema
        assert schema["input_schema"] == tool.parameters

    def test_tool_to_openai_schema(self):
        """Test conversion to OpenAI schema format."""
        tool = DummyTool()
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "dummy_tool"
        assert schema["function"]["description"] == "A dummy tool for testing purposes"
        assert schema["function"]["parameters"] == tool.parameters
