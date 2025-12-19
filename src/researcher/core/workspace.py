"""Workspace management for the Researcher system.

This module provides workspace directory management with:
- Directory creation and validation
- Path resolution (relative to workspace)
- Security checks (prevent access outside workspace)
"""

from pathlib import Path
from typing import Any

from loguru import logger


class WorkspaceManager:
    """Manages workspace directory for agent file operations.

    The workspace is a dedicated directory where agents can freely create, read,
    and modify files. It provides:
    - Automatic workspace creation
    - Relative path resolution
    - Security: prevents access to files outside the workspace

    Attributes:
        workspace_dir: Absolute path to the workspace directory

    Example:
        >>> workspace = WorkspaceManager("./workspace/research_001")
        >>> # Resolve relative path
        >>> abs_path = workspace.resolve_path("data/results.txt")
        >>> # Validate path is within workspace
        >>> if workspace.is_path_safe(abs_path):
        ...     # Proceed with file operation
        ...     pass
    """

    def __init__(self, workspace_dir: str | Path, create_if_missing: bool = True):
        """Initialize workspace manager.

        Args:
            workspace_dir: Path to the workspace directory (can be relative or absolute)
            create_if_missing: If True, create the workspace directory if it doesn't exist

        Raises:
            ValueError: If workspace_dir is empty or invalid
        """
        if not workspace_dir:
            raise ValueError("workspace_dir cannot be empty")

        self.workspace_dir = Path(workspace_dir).resolve()

        if create_if_missing:
            self.ensure_workspace_exists()

        logger.info(f"Workspace initialized at: {self.workspace_dir}")

    def ensure_workspace_exists(self) -> None:
        """Create the workspace directory if it doesn't exist.

        Creates parent directories as needed.
        """
        if not self.workspace_dir.exists():
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created workspace directory: {self.workspace_dir}")

    def resolve_path(self, filepath: str | Path) -> Path:
        """Resolve a file path relative to the workspace.

        If the path is absolute, it's returned as-is (but should be validated with is_path_safe).
        If the path is relative, it's resolved relative to the workspace directory.

        Args:
            filepath: File path (relative or absolute)

        Returns:
            Resolved absolute path

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> workspace.resolve_path("data.txt")
            PosixPath('/absolute/path/to/workspace/data.txt')
            >>> workspace.resolve_path("/tmp/external.txt")
            PosixPath('/tmp/external.txt')  # Still needs safety check!
        """
        path = Path(filepath)

        # If already absolute, return as-is
        if path.is_absolute():
            return path

        # Resolve relative to workspace
        resolved = (self.workspace_dir / path).resolve()
        return resolved

    def is_path_safe(self, filepath: str | Path) -> bool:
        """Check if a file path is within the workspace directory.

        This is a security check to prevent agents from accessing files
        outside their designated workspace.

        Args:
            filepath: File path to check (can be relative or absolute)

        Returns:
            True if the path is within the workspace, False otherwise

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> workspace.is_path_safe("data.txt")
            True
            >>> workspace.is_path_safe("../../../etc/passwd")
            False
        """
        resolved = self.resolve_path(filepath)

        try:
            # Check if resolved path is relative to workspace
            resolved.relative_to(self.workspace_dir)
            return True
        except ValueError:
            # Path is outside workspace
            return False

    def get_relative_path(self, filepath: str | Path) -> Path:
        """Get the relative path from workspace to the given file.

        Args:
            filepath: File path (should be within workspace)

        Returns:
            Path relative to workspace

        Raises:
            ValueError: If the file is not within the workspace

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> workspace.get_relative_path("/workspace/data/file.txt")
            PosixPath('data/file.txt')
        """
        resolved = self.resolve_path(filepath)

        try:
            return resolved.relative_to(self.workspace_dir)
        except ValueError:
            raise ValueError(f"Path {filepath} is not within workspace {self.workspace_dir}")

    def create_subdirectory(self, subdir: str | Path) -> Path:
        """Create a subdirectory within the workspace.

        Args:
            subdir: Subdirectory path relative to workspace

        Returns:
            Absolute path to the created subdirectory

        Raises:
            ValueError: If subdir would be outside the workspace

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> workspace.create_subdirectory("data/processed")
            PosixPath('/absolute/path/to/workspace/data/processed')
        """
        resolved = self.resolve_path(subdir)

        if not self.is_path_safe(resolved):
            raise ValueError(f"Cannot create directory outside workspace: {subdir}")

        resolved.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created subdirectory: {resolved}")
        return resolved

    def list_files(self, pattern: str = "*", recursive: bool = False) -> list[Path]:
        """List files in the workspace matching a pattern.

        Args:
            pattern: Glob pattern (e.g., "*.txt", "**/*.py")
            recursive: If True, search recursively (pattern should use **)

        Returns:
            List of absolute paths to matching files

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> workspace.list_files("*.txt")
            [PosixPath('.../workspace/file1.txt'), PosixPath('.../workspace/file2.txt')]
            >>> workspace.list_files("**/*.md", recursive=True)
            [PosixPath('.../workspace/docs/readme.md'), ...]
        """
        if recursive:
            files = list(self.workspace_dir.rglob(pattern))
        else:
            files = list(self.workspace_dir.glob(pattern))

        # Filter to only files (not directories)
        return [f for f in files if f.is_file()]

    def get_workspace_info(self) -> dict[str, Any]:
        """Get information about the workspace.

        Returns:
            Dict containing workspace metadata

        Example:
            >>> workspace = WorkspaceManager("./workspace")
            >>> info = workspace.get_workspace_info()
            >>> print(info)
            {'path': PosixPath('.../workspace'), 'exists': True, 'is_directory': True, ...}
        """
        info = {
            "path": self.workspace_dir,
            "exists": self.workspace_dir.exists(),
            "is_directory": self.workspace_dir.is_dir() if self.workspace_dir.exists() else False,
        }

        if info["exists"] and info["is_directory"]:
            # Count files and directories
            all_items = list(self.workspace_dir.rglob("*"))
            info["total_files"] = len([f for f in all_items if f.is_file()])
            info["total_directories"] = len([f for f in all_items if f.is_dir()])

        return info

    def clear_workspace(self, confirm: bool = False) -> None:
        """Clear all files in the workspace.

        WARNING: This is a destructive operation!

        Args:
            confirm: Must be True to actually clear the workspace

        Raises:
            ValueError: If confirm is False (safety check)
        """
        if not confirm:
            raise ValueError("Must pass confirm=True to clear workspace (safety check)")

        if not self.workspace_dir.exists():
            logger.warning("Workspace doesn't exist, nothing to clear")
            return

        # Remove all files and subdirectories
        for item in self.workspace_dir.rglob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()

        logger.warning(f"Cleared workspace: {self.workspace_dir}")

    def __str__(self) -> str:
        """String representation of the workspace."""
        return f"WorkspaceManager(workspace_dir={self.workspace_dir})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"WorkspaceManager(workspace_dir='{self.workspace_dir}')"
