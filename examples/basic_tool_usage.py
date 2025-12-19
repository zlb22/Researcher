"""Basic example of creating and using a custom Tool.

This example demonstrates:
1. How to create a custom tool by inheriting from the Tool base class
2. How to define the tool's schema (name, description, parameters)
3. How to implement the execute method
4. How to convert the tool to different LLM provider formats (Anthropic/OpenAI)
"""

import asyncio

from researcher import Tool, ToolResult


class CalculatorTool(Tool):
    """A simple calculator tool that performs basic arithmetic operations."""

    @property
    def name(self) -> str:
        """Tool name used by LLM to invoke the tool."""
        return "calculator"

    @property
    def description(self) -> str:
        """Description helps LLM understand when to use this tool."""
        return "Perform basic arithmetic operations (add, subtract, multiply, divide)"

    @property
    def parameters(self) -> dict:
        """JSON Schema defining the tool's parameters.

        Must follow JSON Schema specification.
        """
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform",
                },
                "a": {"type": "number", "description": "First operand"},
                "b": {"type": "number", "description": "Second operand"},
            },
            "required": ["operation", "a", "b"],
        }

    async def execute(self, operation: str, a: float, b: float) -> ToolResult:
        """Execute the arithmetic operation.

        Args:
            operation: The operation to perform (add/subtract/multiply/divide)
            a: First operand
            b: Second operand

        Returns:
            ToolResult with success status and result content
        """
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolResult(success=False, error="Division by zero")
                result = a / b
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

            return ToolResult(
                success=True,
                content=f"{a} {operation} {b} = {result}",
                metadata={"operation": operation, "result": result},
            )

        except Exception as e:
            return ToolResult(success=False, error=f"Execution error: {str(e)}")


async def main():
    """Demonstrate basic tool usage."""
    # Create an instance of the tool
    calculator = CalculatorTool()

    # Print tool information
    print("=" * 60)
    print("Tool Information:")
    print("=" * 60)
    print(f"Name: {calculator.name}")
    print(f"Description: {calculator.description}")
    print("\nParameters Schema:")
    import json

    print(json.dumps(calculator.parameters, indent=2))

    # Execute the tool
    print("\n" + "=" * 60)
    print("Tool Execution Examples:")
    print("=" * 60)

    # Example 1: Addition
    result = await calculator.execute(operation="add", a=10, b=5)
    print("\n1. Addition:")
    print(f"   Success: {result.success}")
    print(f"   Content: {result.content}")
    print(f"   Metadata: {result.metadata}")

    # Example 2: Division
    result = await calculator.execute(operation="divide", a=20, b=4)
    print("\n2. Division:")
    print(f"   Success: {result.success}")
    print(f"   Content: {result.content}")
    print(f"   Metadata: {result.metadata}")

    # Example 3: Division by zero (error case)
    result = await calculator.execute(operation="divide", a=10, b=0)
    print("\n3. Division by zero (error):")
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")

    # Convert to different LLM formats
    print("\n" + "=" * 60)
    print("LLM Provider Format Conversion:")
    print("=" * 60)

    # Anthropic format
    print("\n1. Anthropic (Claude) Format:")
    anthropic_schema = calculator.to_schema()
    print(json.dumps(anthropic_schema, indent=2))

    # OpenAI format
    print("\n2. OpenAI (GPT) Format:")
    openai_schema = calculator.to_openai_schema()
    print(json.dumps(openai_schema, indent=2))


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
