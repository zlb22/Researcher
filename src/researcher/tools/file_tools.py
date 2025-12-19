"""File operation tools for the Researcher system.

This module provides tools for reading, writing, and editing files within the workspace:
- ReadTool: Read file contents with optional pagination
- WriteTool: Write content to files (create/overwrite/append modes)
- EditTool: Edit files by replacing text
"""

from pathlib import Path
from typing import Any

from loguru import logger

from researcher.core.tool import Tool, ToolResult
from researcher.core.workspace import WorkspaceManager


class ReadTool(Tool):
    """Tool for reading file contents.

    Supports:
    - Reading full file or specific line ranges
    - Line numbering for easy reference
    - Relative paths (resolved to workspace)
    - Safety: only reads files within workspace

    Example:
        >>> workspace = WorkspaceManager("./workspace")
        >>> read_tool = ReadTool(workspace)
        >>> result = await read_tool.execute(filepath="data.txt")
        >>> print(result.content)
    """

    def __init__(self, workspace_manager: WorkspaceManager):
        """Initialize ReadTool.

        Args:
            workspace_manager: WorkspaceManager instance for path resolution
        """
        self.workspace = workspace_manager

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a file. Supports reading full file or specific line ranges. "
            "Returns content with line numbers for easy reference. "
            "File paths can be relative to workspace or absolute (must be within workspace)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace or absolute)",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed, optional). If specified, only read from this line onwards.",
                    "minimum": 1,
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (1-indexed, optional, inclusive). If specified, only read up to this line.",
                    "minimum": 1,
                },
            },
            "required": ["filepath"],
        }

    async def execute(
        self,
        filepath: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> ToolResult:
        """Read file contents.

        Args:
            filepath: Path to the file
            start_line: Starting line number (1-indexed, optional)
            end_line: Ending line number (1-indexed, optional, inclusive)

        Returns:
            ToolResult with file contents (with line numbers) or error
        """
        try:
            # Resolve and validate path
            resolved_path = self.workspace.resolve_path(filepath)

            if not self.workspace.is_path_safe(resolved_path):
                return ToolResult(
                    success=False,
                    error=f"Access denied: {filepath} is outside workspace",
                )

            if not resolved_path.exists():
                return ToolResult(success=False, error=f"File not found: {filepath}")

            if not resolved_path.is_file():
                return ToolResult(success=False, error=f"Not a file: {filepath}")

            # Read file content
            with open(resolved_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Apply line range if specified
            if start_line is not None or end_line is not None:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else total_lines

                # Validate range
                if start_idx < 0 or start_idx >= total_lines:
                    return ToolResult(
                        success=False,
                        error=f"start_line {start_line} out of range (file has {total_lines} lines)",
                    )

                if end_idx < start_idx or end_idx > total_lines:
                    return ToolResult(
                        success=False,
                        error=f"end_line {end_line} invalid (must be >= start_line and <= {total_lines})",
                    )

                selected_lines = lines[start_idx:end_idx]
                first_line_num = start_idx + 1
            else:
                selected_lines = lines
                first_line_num = 1

            # Format with line numbers
            numbered_lines = []
            for i, line in enumerate(selected_lines):
                line_num = first_line_num + i
                # Remove trailing newline for clean formatting
                line_content = line.rstrip("\n")
                numbered_lines.append(f"{line_num:6d}→{line_content}")

            content = "\n".join(numbered_lines)

            # Get relative path for display
            try:
                display_path = self.workspace.get_relative_path(resolved_path)
            except ValueError:
                display_path = resolved_path

            logger.info(f"Read file: {display_path} ({len(selected_lines)} lines)")

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "filepath": str(resolved_path),
                    "relative_path": str(display_path),
                    "total_lines": total_lines,
                    "lines_read": len(selected_lines),
                    "start_line": first_line_num,
                    "end_line": first_line_num + len(selected_lines) - 1,
                },
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                error=f"Cannot read {filepath}: file is not valid UTF-8 text",
            )
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ToolResult(success=False, error=f"Read error: {str(e)}")


class WriteTool(Tool):
    """Tool for writing content to files.

    Supports three modes:
    - create: Create new file (fails if file exists)
    - overwrite: Overwrite existing file (creates if doesn't exist)
    - append: Append to existing file (creates if doesn't exist)

    Example:
        >>> workspace = WorkspaceManager("./workspace")
        >>> write_tool = WriteTool(workspace)
        >>> result = await write_tool.execute(
        ...     filepath="notes.txt",
        ...     content="Hello World",
        ...     mode="create"
        ... )
    """

    def __init__(self, workspace_manager: WorkspaceManager):
        """Initialize WriteTool.

        Args:
            workspace_manager: WorkspaceManager instance for path resolution
        """
        self.workspace = workspace_manager

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            "Write content to a file. Supports three modes: "
            "'create' (create new file, fail if exists), "
            "'overwrite' (replace existing file or create new), "
            "'append' (add to end of file or create new). "
            "File paths can be relative to workspace or absolute (must be within workspace)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace or absolute)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "mode": {
                    "type": "string",
                    "enum": ["create", "overwrite", "append"],
                    "description": "Write mode: 'create' (fail if exists), 'overwrite' (replace), 'append' (add to end)",
                    "default": "create",
                },
            },
            "required": ["filepath", "content"],
        }

    async def execute(self, filepath: str, content: str, mode: str = "create") -> ToolResult:
        """Write content to file.

        Args:
            filepath: Path to the file
            content: Content to write
            mode: Write mode ('create', 'overwrite', or 'append')

        Returns:
            ToolResult indicating success or error
        """
        try:
            # Validate mode
            if mode not in ["create", "overwrite", "append"]:
                return ToolResult(
                    success=False,
                    error=f"Invalid mode: {mode}. Must be 'create', 'overwrite', or 'append'",
                )

            # Resolve and validate path
            resolved_path = self.workspace.resolve_path(filepath)

            if not self.workspace.is_path_safe(resolved_path):
                return ToolResult(
                    success=False,
                    error=f"Access denied: {filepath} is outside workspace",
                )

            # Check file existence based on mode
            file_exists = resolved_path.exists()

            if mode == "create" and file_exists:
                return ToolResult(
                    success=False,
                    error=f"File already exists: {filepath}. Use mode='overwrite' to replace it.",
                )

            # Create parent directories if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            if mode == "append":
                write_mode = "a"
            else:  # create or overwrite
                write_mode = "w"

            with open(resolved_path, write_mode, encoding="utf-8") as f:
                f.write(content)

            # Get file info
            file_size = resolved_path.stat().st_size
            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

            # Get relative path for display
            try:
                display_path = self.workspace.get_relative_path(resolved_path)
            except ValueError:
                display_path = resolved_path

            action = (
                "Created"
                if mode == "create"
                else ("Appended to" if mode == "append" else "Overwrote")
            )
            logger.info(f"{action} file: {display_path} ({file_size} bytes)")

            return ToolResult(
                success=True,
                content=f"{action} {display_path} ({line_count} lines, {file_size} bytes)",
                metadata={
                    "filepath": str(resolved_path),
                    "relative_path": str(display_path),
                    "mode": mode,
                    "bytes_written": file_size,
                    "line_count": line_count,
                },
            )

        except Exception as e:
            logger.error(f"Error writing file {filepath}: {e}")
            return ToolResult(success=False, error=f"Write error: {str(e)}")


class EditTool(Tool):
    """Tool for editing files by replacing text.

    Finds and replaces text in a file. The old_string must match exactly
    and must be unique in the file (to prevent accidental replacements).

    Example:
        >>> workspace = WorkspaceManager("./workspace")
        >>> edit_tool = EditTool(workspace)
        >>> result = await edit_tool.execute(
        ...     filepath="config.py",
        ...     old_string="DEBUG = False",
        ...     new_string="DEBUG = True"
        ... )
    """

    def __init__(self, workspace_manager: WorkspaceManager):
        """Initialize EditTool.

        Args:
            workspace_manager: WorkspaceManager instance for path resolution
        """
        self.workspace = workspace_manager

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return (
            "Edit a file by replacing text. The old_string must match exactly and "
            "must appear exactly once in the file (to prevent accidental replacements). "
            "File paths can be relative to workspace or absolute (must be within workspace)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace or absolute)",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to find and replace (must be unique in file)",
                },
                "new_string": {
                    "type": "string",
                    "description": "Text to replace old_string with",
                },
            },
            "required": ["filepath", "old_string", "new_string"],
        }

    async def execute(self, filepath: str, old_string: str, new_string: str) -> ToolResult:
        """Edit file by replacing text.

        Args:
            filepath: Path to the file
            old_string: Text to find (must be unique)
            new_string: Text to replace with

        Returns:
            ToolResult indicating success or error
        """
        try:
            # Resolve and validate path
            resolved_path = self.workspace.resolve_path(filepath)

            if not self.workspace.is_path_safe(resolved_path):
                return ToolResult(
                    success=False,
                    error=f"Access denied: {filepath} is outside workspace",
                )

            if not resolved_path.exists():
                return ToolResult(success=False, error=f"File not found: {filepath}")

            if not resolved_path.is_file():
                return ToolResult(success=False, error=f"Not a file: {filepath}")

            # Read current content
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if old_string exists
            if old_string not in content:
                return ToolResult(
                    success=False,
                    error=f"old_string not found in file: {old_string[:100]}{'...' if len(old_string) > 100 else ''}",
                )

            # Count occurrences
            occurrence_count = content.count(old_string)
            if occurrence_count > 1:
                return ToolResult(
                    success=False,
                    error=f"old_string appears {occurrence_count} times in file. "
                    f"It must be unique to prevent accidental replacements.",
                )

            # Perform replacement
            new_content = content.replace(old_string, new_string)

            # Write back
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Get relative path for display
            try:
                display_path = self.workspace.get_relative_path(resolved_path)
            except ValueError:
                display_path = resolved_path

            logger.info(f"Edited file: {display_path}")

            return ToolResult(
                success=True,
                content=f"Edited {display_path}: replaced 1 occurrence",
                metadata={
                    "filepath": str(resolved_path),
                    "relative_path": str(display_path),
                    "old_length": len(old_string),
                    "new_length": len(new_string),
                    "size_change": len(new_content) - len(content),
                },
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                error=f"Cannot edit {filepath}: file is not valid UTF-8 text",
            )
        except Exception as e:
            logger.error(f"Error editing file {filepath}: {e}")
            return ToolResult(success=False, error=f"Edit error: {str(e)}")
