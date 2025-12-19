"""Example demonstrating file operation tools.

This example shows how to:
1. Create and manage a workspace
2. Use ReadTool, WriteTool, and EditTool
3. Handle errors and work with file metadata
"""

import asyncio
import tempfile
from pathlib import Path

from researcher.core.workspace import WorkspaceManager
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool


async def main():
    """Demonstrate file tools usage."""
    # Create a temporary workspace for this demo
    with tempfile.TemporaryDirectory() as tmpdir:
        print("=" * 70)
        print("File Tools Demo")
        print("=" * 70)

        # Initialize workspace
        workspace = WorkspaceManager(tmpdir)
        print(f"\nWorkspace: {workspace.workspace_dir}")

        # Create tool instances
        write_tool = WriteTool(workspace)
        read_tool = ReadTool(workspace)
        edit_tool = EditTool(workspace)

        # ===== WriteTool Demo =====
        print("\n" + "=" * 70)
        print("1. WriteTool - Creating a new file")
        print("=" * 70)

        result = await write_tool.execute(
            filepath="notes.txt",
            content="Meeting Notes - 2025-12-19\n\nAttendees:\n- Alice\n- Bob\n\nTopics:\n1. Project status\n2. Next steps\n",
            mode="create",
        )

        print(f"Success: {result.success}")
        print(f"Message: {result.content}")
        print(f"Metadata: {result.metadata}")

        # ===== ReadTool Demo =====
        print("\n" + "=" * 70)
        print("2. ReadTool - Reading the file")
        print("=" * 70)

        result = await read_tool.execute(filepath="notes.txt")

        print(f"Success: {result.success}")
        print(f"\nFile contents:\n{result.content}")
        print(f"\nMetadata: {result.metadata}")

        # ===== ReadTool with Line Range =====
        print("\n" + "=" * 70)
        print("3. ReadTool - Reading specific line range (lines 3-5)")
        print("=" * 70)

        result = await read_tool.execute(filepath="notes.txt", start_line=3, end_line=5)

        print(f"Success: {result.success}")
        print(f"\nPartial contents:\n{result.content}")

        # ===== WriteTool Append Mode =====
        print("\n" + "=" * 70)
        print("4. WriteTool - Appending to the file")
        print("=" * 70)

        result = await write_tool.execute(
            filepath="notes.txt",
            content="\nAction Items:\n- [ ] Review code\n- [ ] Update docs\n",
            mode="append",
        )

        print(f"Success: {result.success}")
        print(f"Message: {result.content}")

        # Read again to see the change
        result = await read_tool.execute(filepath="notes.txt")
        print(f"\nUpdated file contents:\n{result.content}")

        # ===== EditTool Demo =====
        print("\n" + "=" * 70)
        print("5. EditTool - Editing the file (replacing text)")
        print("=" * 70)

        result = await edit_tool.execute(
            filepath="notes.txt",
            old_string="- Alice\n- Bob",
            new_string="- Alice\n- Bob\n- Charlie",
        )

        print(f"Success: {result.success}")
        print(f"Message: {result.content}")
        print(f"Metadata: {result.metadata}")

        # Read to verify the edit
        result = await read_tool.execute(filepath="notes.txt")
        print(f"\nFile after edit:\n{result.content}")

        # ===== Workspace Organization =====
        print("\n" + "=" * 70)
        print("6. Organizing files in subdirectories")
        print("=" * 70)

        # Create files in subdirectories
        await write_tool.execute(
            filepath="research/topic_1/summary.md",
            content="# Topic 1 Summary\n\nKey findings...\n",
            mode="create",
        )

        await write_tool.execute(
            filepath="research/topic_1/details.md",
            content="# Topic 1 Details\n\nDetailed analysis...\n",
            mode="create",
        )

        await write_tool.execute(
            filepath="research/topic_2/summary.md",
            content="# Topic 2 Summary\n\nKey findings...\n",
            mode="create",
        )

        print("Created files in subdirectories:")
        files = workspace.list_files("**/*.md", recursive=True)
        for file in files:
            rel_path = workspace.get_relative_path(file)
            print(f"  - {rel_path}")

        # ===== Error Handling Demo =====
        print("\n" + "=" * 70)
        print("7. Error Handling Examples")
        print("=" * 70)

        # Try to read non-existent file
        print("\n7a. Reading non-existent file:")
        result = await read_tool.execute(filepath="nonexistent.txt")
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # Try to create file that already exists
        print("\n7b. Creating file that already exists:")
        result = await write_tool.execute(
            filepath="notes.txt", content="New content", mode="create"
        )
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # Try to edit with non-existent string
        print("\n7c. Editing with string not found:")
        result = await edit_tool.execute(
            filepath="notes.txt",
            old_string="This string does not exist",
            new_string="New text",
        )
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # Try to edit with non-unique string (create file with duplicates)
        await write_tool.execute(
            filepath="duplicates.txt",
            content="Hello\nHello\nHello\n",
            mode="create",
        )

        print("\n7d. Editing with non-unique string:")
        result = await edit_tool.execute(
            filepath="duplicates.txt",
            old_string="Hello",
            new_string="Goodbye",
        )
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # ===== Security: Access Outside Workspace =====
        print("\n" + "=" * 70)
        print("8. Security - Preventing access outside workspace")
        print("=" * 70)

        # Try to write outside workspace
        print("\n8a. Attempting to write outside workspace:")
        result = await write_tool.execute(
            filepath="/tmp/evil.txt", content="Evil content", mode="create"
        )
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # Try to read outside workspace
        print("\n8b. Attempting to read outside workspace:")
        result = await read_tool.execute(filepath="/etc/passwd")
        print(f"Success: {result.success}")
        print(f"Error: {result.error}")

        # ===== Workspace Info =====
        print("\n" + "=" * 70)
        print("9. Workspace Information")
        print("=" * 70)

        info = workspace.get_workspace_info()
        print(f"Path: {info['path']}")
        print(f"Exists: {info['exists']}")
        print(f"Total files: {info['total_files']}")
        print(f"Total directories: {info['total_directories']}")

        print("\n" + "=" * 70)
        print("Demo Complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
