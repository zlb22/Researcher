"""Tests for file operation tools."""

import tempfile
from pathlib import Path

import pytest

from researcher.core.workspace import WorkspaceManager
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = WorkspaceManager(tmpdir)
        yield workspace


@pytest.fixture
def read_tool(temp_workspace):
    """Create a ReadTool instance with temp workspace."""
    return ReadTool(temp_workspace)


@pytest.fixture
def write_tool(temp_workspace):
    """Create a WriteTool instance with temp workspace."""
    return WriteTool(temp_workspace)


@pytest.fixture
def edit_tool(temp_workspace):
    """Create an EditTool instance with temp workspace."""
    return EditTool(temp_workspace)


class TestReadTool:
    """Test ReadTool functionality."""

    async def test_read_simple_file(self, temp_workspace, read_tool):
        """Test reading a simple text file."""
        # Create a test file
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        # Read the file
        result = await read_tool.execute(filepath="test.txt")

        assert result.success is True
        assert "Line 1" in result.content
        assert "Line 2" in result.content
        assert "Line 3" in result.content
        assert result.metadata["total_lines"] == 3
        assert result.metadata["lines_read"] == 3

    async def test_read_with_line_range(self, temp_workspace, read_tool):
        """Test reading specific line range."""
        # Create a test file
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        # Read lines 2-4
        result = await read_tool.execute(filepath="test.txt", start_line=2, end_line=4)

        assert result.success is True
        assert "Line 2" in result.content
        assert "Line 3" in result.content
        assert "Line 4" in result.content
        assert "Line 1" not in result.content
        assert "Line 5" not in result.content
        assert result.metadata["lines_read"] == 3

    async def test_read_nonexistent_file(self, read_tool):
        """Test reading a file that doesn't exist."""
        result = await read_tool.execute(filepath="nonexistent.txt")

        assert result.success is False
        assert "not found" in result.error.lower()

    async def test_read_file_outside_workspace(self, temp_workspace, read_tool):
        """Test that reading outside workspace is blocked."""
        result = await read_tool.execute(filepath="/etc/passwd")

        assert result.success is False
        assert "outside workspace" in result.error.lower()

    async def test_read_with_invalid_line_range(self, temp_workspace, read_tool):
        """Test reading with invalid line range."""
        # Create a test file with 3 lines
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        # Try to read lines starting from line 10
        result = await read_tool.execute(filepath="test.txt", start_line=10)

        assert result.success is False
        assert "out of range" in result.error.lower()


class TestWriteTool:
    """Test WriteTool functionality."""

    async def test_write_create_new_file(self, write_tool):
        """Test creating a new file."""
        result = await write_tool.execute(
            filepath="new_file.txt", content="Hello World", mode="create"
        )

        assert result.success is True
        assert "Created" in result.content
        assert result.metadata["mode"] == "create"

    async def test_write_create_existing_file_fails(self, temp_workspace, write_tool):
        """Test that create mode fails if file exists."""
        # Create a file first
        test_file = temp_workspace.workspace_dir / "existing.txt"
        test_file.write_text("Original content")

        # Try to create again
        result = await write_tool.execute(
            filepath="existing.txt", content="New content", mode="create"
        )

        assert result.success is False
        assert "already exists" in result.error.lower()

    async def test_write_overwrite_mode(self, temp_workspace, write_tool):
        """Test overwrite mode."""
        # Create a file first
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Original content")

        # Overwrite it
        result = await write_tool.execute(
            filepath="test.txt", content="New content", mode="overwrite"
        )

        assert result.success is True
        assert "Overwrote" in result.content

        # Verify content was replaced
        assert test_file.read_text() == "New content"

    async def test_write_append_mode(self, temp_workspace, write_tool):
        """Test append mode."""
        # Create a file first
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Original content\n")

        # Append to it
        result = await write_tool.execute(
            filepath="test.txt", content="Appended content\n", mode="append"
        )

        assert result.success is True
        assert "Appended" in result.content

        # Verify content was appended
        content = test_file.read_text()
        assert "Original content" in content
        assert "Appended content" in content

    async def test_write_creates_parent_directories(self, temp_workspace, write_tool):
        """Test that write creates parent directories."""
        result = await write_tool.execute(
            filepath="subdir/nested/file.txt",
            content="Hello",
            mode="create",
        )

        assert result.success is True

        # Verify file and directories were created
        file_path = temp_workspace.workspace_dir / "subdir" / "nested" / "file.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello"

    async def test_write_outside_workspace_fails(self, write_tool):
        """Test that writing outside workspace is blocked."""
        result = await write_tool.execute(
            filepath="/tmp/evil.txt", content="Evil content", mode="create"
        )

        assert result.success is False
        assert "outside workspace" in result.error.lower()


class TestEditTool:
    """Test EditTool functionality."""

    async def test_edit_simple_replacement(self, temp_workspace, edit_tool):
        """Test simple text replacement."""
        # Create a test file
        test_file = temp_workspace.workspace_dir / "config.txt"
        test_file.write_text("DEBUG = False\nVERBOSE = True\n")

        # Edit it
        result = await edit_tool.execute(
            filepath="config.txt",
            old_string="DEBUG = False",
            new_string="DEBUG = True",
        )

        assert result.success is True
        assert "replaced 1 occurrence" in result.content.lower()

        # Verify content was changed
        content = test_file.read_text()
        assert "DEBUG = True" in content
        assert "DEBUG = False" not in content

    async def test_edit_nonexistent_file(self, edit_tool):
        """Test editing a file that doesn't exist."""
        result = await edit_tool.execute(
            filepath="nonexistent.txt",
            old_string="old",
            new_string="new",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    async def test_edit_string_not_found(self, temp_workspace, edit_tool):
        """Test editing with a string that doesn't exist in file."""
        # Create a test file
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Hello World")

        # Try to replace non-existent string
        result = await edit_tool.execute(
            filepath="test.txt",
            old_string="Goodbye",
            new_string="Hello",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    async def test_edit_non_unique_string_fails(self, temp_workspace, edit_tool):
        """Test that editing non-unique string fails."""
        # Create a test file with duplicate text
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Hello\nHello\nHello\n")

        # Try to replace non-unique string
        result = await edit_tool.execute(
            filepath="test.txt",
            old_string="Hello",
            new_string="Goodbye",
        )

        assert result.success is False
        assert "3 times" in result.error
        assert "unique" in result.error.lower()

    async def test_edit_multiline_replacement(self, temp_workspace, edit_tool):
        """Test editing multiline text."""
        # Create a test file
        test_file = temp_workspace.workspace_dir / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\n")

        # Replace multiline text
        result = await edit_tool.execute(
            filepath="test.txt",
            old_string="Line 2\nLine 3",
            new_string="Modified Line 2\nModified Line 3",
        )

        assert result.success is True

        # Verify replacement
        content = test_file.read_text()
        assert "Modified Line 2" in content
        assert "Modified Line 3" in content
        # Verify the exact lines are replaced (not just checking substring)
        lines = content.split("\n")
        assert any("Modified Line 2" == line for line in lines)
        assert any("Modified Line 3" == line for line in lines)

    async def test_edit_outside_workspace_fails(self, edit_tool):
        """Test that editing outside workspace is blocked."""
        result = await edit_tool.execute(
            filepath="/etc/passwd",
            old_string="root",
            new_string="evil",
        )

        assert result.success is False
        assert "outside workspace" in result.error.lower()


class TestWorkspaceIntegration:
    """Test integration of file tools with workspace."""

    async def test_relative_path_resolution(self, temp_workspace, write_tool, read_tool):
        """Test that relative paths are resolved correctly."""
        # Write with relative path
        write_result = await write_tool.execute(
            filepath="data/results.txt", content="Test data", mode="create"
        )
        assert write_result.success is True

        # Read with relative path
        read_result = await read_tool.execute(filepath="data/results.txt")
        assert read_result.success is True
        assert "Test data" in read_result.content

    async def test_full_workflow(self, temp_workspace, write_tool, read_tool, edit_tool):
        """Test a complete workflow: write -> read -> edit -> read."""
        # Step 1: Write a file
        write_result = await write_tool.execute(
            filepath="workflow.txt",
            content="Version: 1.0\nStatus: draft\n",
            mode="create",
        )
        assert write_result.success is True

        # Step 2: Read it
        read_result = await read_tool.execute(filepath="workflow.txt")
        assert read_result.success is True
        assert "Version: 1.0" in read_result.content

        # Step 3: Edit it
        edit_result = await edit_tool.execute(
            filepath="workflow.txt",
            old_string="Status: draft",
            new_string="Status: final",
        )
        assert edit_result.success is True

        # Step 4: Read again to verify
        final_result = await read_tool.execute(filepath="workflow.txt")
        assert final_result.success is True
        assert "Status: final" in final_result.content
        assert "Status: draft" not in final_result.content
