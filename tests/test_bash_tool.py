"""Tests for BashTool."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from researcher.core.workspace import WorkspaceManager
from researcher.tools.bash_tool import BashTool


@pytest.fixture
def workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = WorkspaceManager(tmpdir)
        yield workspace


@pytest.fixture
def bash_tool(workspace):
    """Create a BashTool instance for testing."""
    return BashTool(workspace)


class TestBashTool:
    """Test suite for BashTool."""

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, bash_tool):
        """Test executing a simple command."""
        result = await bash_tool.execute(command="echo 'Hello, World!'")

        assert result.success is True
        assert "Hello, World!" in result.content
        assert result.metadata["exit_code"] == 0
        assert result.metadata["timed_out"] is False

    @pytest.mark.asyncio
    async def test_execute_ls_command(self, bash_tool, workspace):
        """Test ls command in workspace."""
        # Create some test files
        test_file = workspace.workspace_dir / "test.txt"
        test_file.write_text("test content")

        result = await bash_tool.execute(command="ls -la")

        assert result.success is True
        assert "test.txt" in result.content
        assert result.metadata["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_stderr(self, bash_tool):
        """Test command that outputs to stderr."""
        # ls on nonexistent file produces stderr
        result = await bash_tool.execute(command="ls /nonexistent_path_12345")

        assert result.success is False  # Non-zero exit code
        assert result.metadata["exit_code"] != 0
        assert "stderr" in result.metadata
        assert len(result.metadata["stderr"]) > 0

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, bash_tool):
        """Test command timeout."""
        # Sleep for 5 seconds but timeout after 1 second
        result = await bash_tool.execute(command="sleep 5", timeout=1)

        assert result.success is False
        assert "timed out" in result.error.lower()
        assert result.metadata["timed_out"] is True

    @pytest.mark.asyncio
    async def test_execute_in_workspace_directory(self, bash_tool, workspace):
        """Test that commands execute in workspace directory."""
        # Create a file in workspace
        test_file = workspace.workspace_dir / "marker.txt"
        test_file.write_text("marker")

        # pwd should show workspace directory
        result = await bash_tool.execute(command="pwd")

        assert result.success is True
        assert str(workspace.workspace_dir) in result.content

        # Should be able to see the marker file
        result = await bash_tool.execute(command="ls marker.txt")
        assert result.success is True
        assert "marker.txt" in result.content

    @pytest.mark.asyncio
    async def test_execute_piped_commands(self, bash_tool, workspace):
        """Test executing piped commands."""
        # Create test files
        file1 = workspace.workspace_dir / "file1.txt"
        file2 = workspace.workspace_dir / "file2.txt"
        file1.write_text("apple\nbanana\ncherry")
        file2.write_text("dog\nelephant\nfox")

        # Use pipe and grep
        result = await bash_tool.execute(command="cat file1.txt | grep banana")

        assert result.success is True
        assert "banana" in result.content
        assert "apple" not in result.content or result.content.count("apple") == 0

    @pytest.mark.asyncio
    async def test_execute_creates_files(self, bash_tool, workspace):
        """Test command that creates files."""
        result = await bash_tool.execute(command="echo 'test content' > output.txt")

        assert result.success is True

        # Verify file was created
        output_file = workspace.workspace_dir / "output.txt"
        assert output_file.exists()
        assert "test content" in output_file.read_text()

    @pytest.mark.asyncio
    async def test_execute_empty_command(self, bash_tool):
        """Test executing empty command."""
        result = await bash_tool.execute(command="")

        assert result.success is False
        assert "must not be empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_invalid_timeout(self, bash_tool):
        """Test executing with invalid timeout."""
        # Timeout too small
        result = await bash_tool.execute(command="echo test", timeout=0)
        assert result.success is False
        assert "timeout" in result.error.lower()

        # Timeout too large
        result = await bash_tool.execute(command="echo test", timeout=1000)
        assert result.success is False
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_command_with_no_output(self, bash_tool, workspace):
        """Test command that produces no output."""
        # Create a file silently
        result = await bash_tool.execute(command="touch silent.txt")

        assert result.success is True
        assert result.content == "(no output)" or result.content.strip() == ""

        # Verify file was created
        assert (workspace.workspace_dir / "silent.txt").exists()

    @pytest.mark.asyncio
    async def test_tool_properties(self, bash_tool):
        """Test tool properties."""
        assert bash_tool.name == "execute_shell"
        assert "shell command" in bash_tool.description.lower()

        params = bash_tool.parameters
        assert params["type"] == "object"
        assert "command" in params["properties"]
        assert "timeout" in params["properties"]
        assert "command" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_with_exit_code(self, bash_tool):
        """Test command with specific exit code."""
        # Use exit command to set specific exit code
        result = await bash_tool.execute(command="exit 42")

        assert result.success is False
        assert result.metadata["exit_code"] == 42
        assert "exited with code 42" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_multiple_commands(self, bash_tool, workspace):
        """Test executing multiple commands with &&."""
        result = await bash_tool.execute(
            command="echo 'first' > file1.txt && echo 'second' > file2.txt"
        )

        assert result.success is True

        # Verify both files were created
        assert (workspace.workspace_dir / "file1.txt").exists()
        assert (workspace.workspace_dir / "file2.txt").exists()

    @pytest.mark.asyncio
    async def test_output_truncation(self, bash_tool):
        """Test that very long output gets truncated."""
        # Generate output longer than MAX_OUTPUT_LENGTH
        max_len = bash_tool.MAX_OUTPUT_LENGTH
        # Create a command that outputs many lines
        long_command = "for i in {1..10000}; do echo 'This is line number '$i; done"

        result = await bash_tool.execute(command=long_command)

        assert result.success is True
        # Output should be truncated
        if len(result.metadata["stdout"]) > max_len:
            assert "truncated" in result.metadata["stdout"].lower()
