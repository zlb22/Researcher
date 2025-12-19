"""Control tools for agent execution flow.

This module provides tools that control agent behavior and execution flow,
such as explicitly marking task completion.
"""

from typing import Any

from researcher.core.tool import Tool, ToolResult


class CompleteTool(Tool):
    """Tool for explicitly marking task completion.

    This tool allows agents to explicitly signal when a task is complete,
    indicating whether it succeeded or failed. This prevents ambiguous
    termination states where the agent stops without clear indication
    of success or failure.

    Example:
        >>> complete = CompleteTool()
        >>> result = await complete.execute(
        ...     success=True,
        ...     summary="Task completed successfully. Created 3 files."
        ... )
        >>> assert result.success == True
    """

    @property
    def name(self) -> str:
        """Tool name."""
        return "complete_task"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Mark task as completed (success or failure). "
            "MUST be called when task is finished. "
            "Use success=True for successful completion, "
            "success=False for failures or insurmountable problems."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the task completed successfully",
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was accomplished or why it failed",
                },
            },
            "required": ["success", "summary"],
        }

    async def execute(self, success: bool, summary: str) -> ToolResult:
        """Execute the complete task tool.

        Args:
            success: Whether the task succeeded
            summary: Summary of task completion

        Returns:
            ToolResult with the completion status and summary

        Example:
            >>> result = await complete.execute(
            ...     success=True,
            ...     summary="Created and modified notes.txt successfully"
            ... )
        """
        return ToolResult(
            success=success,
            content=summary,
            metadata={"explicitly_completed": True},
        )
