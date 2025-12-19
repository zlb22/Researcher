"""Simple agent example demonstrating basic agent usage.

This example shows how to:
1. Create an LLM client (Anthropic Claude)
2. Set up tools for the agent
3. Initialize a BaseAgent
4. Run a task with the agent

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Example: export ANTHROPIC_API_KEY="sk-ant-..."
"""

import asyncio
import os
import tempfile

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm.anthropic_client import AnthropicClient
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.utils.logger import configure_logger
from researcher.utils.prompt_loader import PromptLoader


async def main():
    """Demonstrate simple agent usage."""
    # Configure logger
    configure_logger(level="INFO")

    print("=" * 70)
    print("Simple Agent Demo")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set\n")
        print("Please set your API key:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        print("\nOr set it in your script:")
        print('  os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."')
        return

    # Create a temporary workspace for this demo
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nWorkspace: {tmpdir}\n")

        # 1. Initialize LLM client
        print("1. Initializing LLM client (Anthropic Claude)...")
        llm_client = AnthropicClient(
            api_key=api_key,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
        )

        # 2. Create workspace and tools
        print("2. Setting up workspace and tools...")
        workspace = WorkspaceManager(tmpdir)
        tools = [
            ReadTool(workspace),
            WriteTool(workspace),
            EditTool(workspace),
            CompleteTool(),
        ]

        # 3. Load system prompt
        print("3. Loading system prompt...")
        prompt_loader = PromptLoader()
        system_prompt = prompt_loader.load("test_agent")

        # 4. Initialize agent
        print("4. Initializing agent...")
        agent = BaseAgent(
            agent_type="test_agent",
            system_prompt=system_prompt,
            llm_client=llm_client,
            tools=tools,
            workspace_dir=tmpdir,
            max_steps=10,
        )

        # 5. Run a simple task
        print("\n" + "=" * 70)
        print("Running Task: Create and modify a file")
        print("=" * 70 + "\n")

        task = """Please do the following:
1. Create a file called 'notes.txt' with the content: "Hello from the agent!"
2. Read the file to verify it was created
3. Edit the file to change "Hello" to "Greetings"
4. Read the file again to confirm the change
"""

        result = await agent.run(task)

        # 6. Display result
        print("\n" + "=" * 70)
        print("Task Result")
        print("=" * 70)
        print(f"Success: {result.success}")
        print(f"\nAgent Response:\n{result.content}")
        print("\nMetadata:")
        for key, value in result.metadata.items():
            print(f"  {key}: {value}")

        # 7. Show workspace contents
        print("\n" + "=" * 70)
        print("Workspace Contents")
        print("=" * 70)
        files = workspace.list_files("**/*", recursive=True)
        if files:
            for file in files:
                rel_path = workspace.get_relative_path(file)
                print(f"\n📄 {rel_path}")
                print("-" * 70)
                with open(file, "r") as f:
                    print(f.read())
        else:
            print("(no files created)")

        print("\n" + "=" * 70)
        print("Demo Complete!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
