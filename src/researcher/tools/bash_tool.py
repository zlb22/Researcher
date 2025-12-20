"""Shell command execution tools for the Researcher system.

This module provides tools for executing shell commands, allowing agents
to interact with the file system and run external programs.
"""

import asyncio
import shlex
from pathlib import Path
from typing import Any

from loguru import logger

from researcher.core.tool import Tool, ToolResult


class BashTool(Tool):
    """Tool for executing shell commands in a workspace.

    This tool allows agents to run shell commands for tasks like:
    - Exploring directory structure (ls, find, tree)
    - Searching file contents (grep, cat)
    - File operations (mkdir, mv, cp)
    - Running scripts and external programs

    Security considerations:
    - Commands execute in the workspace directory by default
    - Timeout protection prevents infinite execution
    - Interactive commands (vim, nano, etc.) are not supported
    - Stdout and stderr are captured and returned

    Example:
        >>> workspace = WorkspaceManager("/path/to/workspace")
        >>> bash = BashTool(workspace)
        >>> result = await bash.execute(command="ls -la")
        >>> print(result.content)  # Command output
    """

    DEFAULT_TIMEOUT = 120  # seconds
    MAX_OUTPUT_LENGTH = 50000  # characters

    def __init__(
        self,
        workspace: Any,  # WorkspaceManager
        default_timeout: int | None = None,
    ):
        """Initialize the Bash tool.

        Args:
            workspace: WorkspaceManager instance for path resolution
            default_timeout: Default timeout in seconds (default: 120)
        """
        self.workspace = workspace
        self.default_timeout = default_timeout or self.DEFAULT_TIMEOUT

    @property
    def name(self) -> str:
        """Tool name."""
        return "execute_shell"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Execute a shell command in the workspace directory. "
            "Use this to explore files (ls, find), search contents (grep, cat), "
            "run scripts, or perform file operations (mkdir, mv, cp). "
            "Commands run with a timeout and are non-interactive. "
            "Returns stdout and stderr output."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "Shell command to execute. Examples: 'ls -la', "
                        "'grep -r keyword .', 'find . -name \"*.md\"'"
                    ),
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 600,
                    "default": self.DEFAULT_TIMEOUT,
                    "description": (
                        f"Timeout in seconds (1-600, default {self.DEFAULT_TIMEOUT}). "
                        "Command will be terminated if it runs longer."
                    ),
                },
            },
            "required": ["command"],
        }

    async def execute(
        self,
        command: str,
        timeout: int | None = None,
    ) -> ToolResult:
        """Execute a shell command.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds (default: from initialization)

        Returns:
            ToolResult with:
            - success: True if command completed (exit code 0)
            - content: Combined stdout and stderr output
            - metadata: {
                "exit_code": int,
                "stdout": str,
                "stderr": str,
                "timed_out": bool,
                "command": str
            }

        Example:
            >>> result = await bash.execute(command="ls -la")
            >>> if result.success:
            ...     print(result.content)
        """
        # Validate command
        if not command or not command.strip():
            return ToolResult(
                success=False,
                error="Command must not be empty",
            )

        # Validate timeout
        if timeout is None:
            timeout = self.default_timeout
        elif timeout < 1 or timeout > 600:
            return ToolResult(
                success=False,
                error="Timeout must be between 1 and 600 seconds",
            )

        command = command.strip()
        logger.info(
            f"Executing shell command: {command[:100]}{'...' if len(command) > 100 else ''}"
        )

        # Execute command in workspace directory
        try:
            result = await self._run_command(command, timeout)
            return result
        except Exception as e:
            logger.error(f"Shell command failed with exception: {e}")
            return ToolResult(
                success=False,
                error=f"Command execution failed: {str(e)}",
                metadata={"command": command},
            )

    async def _run_command(
        self,
        command: str,
        timeout: int,
    ) -> ToolResult:
        """Run a shell command and capture output.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds

        Returns:
            ToolResult with execution results
        """
        # Create subprocess
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace.workspace_dir),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to start command: {str(e)}",
                metadata={"command": command},
            )

        # Wait for completion with timeout
        timed_out = False
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            # Kill process on timeout
            timed_out = True
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass

            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout} seconds",
                metadata={
                    "command": command,
                    "timeout": timeout,
                    "timed_out": True,
                },
            )

        # Decode output
        try:
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to decode command output: {str(e)}",
                metadata={"command": command},
            )

        # Get exit code
        exit_code = process.returncode or 0

        # Truncate output if too long
        if len(stdout) > self.MAX_OUTPUT_LENGTH:
            stdout = (
                stdout[: self.MAX_OUTPUT_LENGTH]
                + f"\n\n[Output truncated at {self.MAX_OUTPUT_LENGTH} characters]"
            )
        if len(stderr) > self.MAX_OUTPUT_LENGTH:
            stderr = (
                stderr[: self.MAX_OUTPUT_LENGTH]
                + f"\n\n[Output truncated at {self.MAX_OUTPUT_LENGTH} characters]"
            )

        # Build result
        success = exit_code == 0
        combined_output = ""

        if stdout:
            combined_output += stdout
        if stderr:
            if combined_output:
                combined_output += "\n--- stderr ---\n"
            combined_output += stderr

        if not combined_output:
            combined_output = "(no output)"

        metadata = {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": timed_out,
        }

        if success:
            logger.debug(
                f"Command succeeded (exit code {exit_code}), output length: {len(combined_output)}"
            )
            return ToolResult(
                success=True,
                content=combined_output,
                metadata=metadata,
            )
        else:
            logger.warning(f"Command failed with exit code {exit_code}")
            return ToolResult(
                success=False,
                content=combined_output,
                error=f"Command exited with code {exit_code}",
                metadata=metadata,
            )
