"""Simple agent example demonstrating basic agent usage.

This example shows how to:
1. Create an LLM client (Anthropic Claude or OpenAI-compatible)
2. Set up tools for the agent
3. Initialize a BaseAgent
4. Run a task with the agent

Requirements:
- Set ANTHROPIC_API_KEY for Anthropic Claude
- Or set OPENAI_API_KEY (+ optional OPENAI_BASE_URL/OPENAI_MODEL) for OpenAI-compatible
- See .env.example for details
"""

import asyncio
import os
import tempfile

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm import AnthropicClient, OpenAIClient
from researcher.llm.base import LLMClient
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.utils.logger import configure_logger
from researcher.utils.prompt_loader import PromptLoader


def build_llm_client(max_tokens: int = 4096) -> tuple[LLMClient | None, str | None]:
    """Create an LLM client using available environment variables."""
    anthropic_configured = os.getenv("ANTHROPIC_API_KEY") is not None
    openai_configured = os.getenv("OPENAI_API_KEY") is not None

    provider: str | None = None

    if anthropic_configured and openai_configured:
        print("Select LLM provider:")
        print("1. Anthropic Claude")
        print("2. OpenAI / OpenAI-compatible")
        choice = input("Enter 1 or 2 [1]: ").strip() or "1"
        provider = "openai" if choice == "2" else "anthropic"
    elif anthropic_configured:
        provider = "anthropic"
    elif openai_configured:
        provider = "openai"
    else:
        print("\n❌ Error: No LLM provider configured.\n")
        print("Set one of the following environment variables:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        print('  export OPENAI_API_KEY="sk-..."  # + optional OPENAI_BASE_URL')
        print("\nRefer to .env.example for more options.\n")
        return None, None

    if provider == "anthropic":
        return AnthropicClient(max_tokens=max_tokens), "Anthropic Claude"

    return OpenAIClient(max_tokens=max_tokens), "OpenAI-compatible"


async def main():
    """Demonstrate simple agent usage."""
    # Configure logger
    configure_logger(level="INFO")

    print("=" * 70)
    print("Simple Agent Demo")
    print("=" * 70)

    # Initialize LLM client
    print("1. Initializing LLM client...")
    llm_client, provider_name = build_llm_client(max_tokens=4096)
    if llm_client is None or provider_name is None:
        return
    print(f"   -> Using {provider_name}\n")

    # Create a temporary workspace for this demo
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nWorkspace: {tmpdir}\n")

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
