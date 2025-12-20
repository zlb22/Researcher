"""Writer agent for creating research reports and documents.

This module provides the Writer agent, which specializes in:
- Reading research materials and analysis
- Creating well-structured, clear documents
- Ensuring logical flow and proper citations
- Supporting iterative refinement
"""

from pathlib import Path

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm.base import LLMClient
from researcher.tools.bash_tool import BashTool
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.utils.prompt_loader import PromptLoader


def create_writer(
    llm_client: LLMClient,
    workspace_dir: str | Path,
    max_steps: int = 50,
) -> BaseAgent:
    """Create a Writer agent.

    The Writer agent is responsible for:
    - Creating clear, well-structured research reports
    - Organizing information for readability
    - Citing sources appropriately
    - Iterative document refinement

    Args:
        llm_client: LLM client for the agent
        workspace_dir: Workspace directory for file operations
        max_steps: Maximum number of agent steps (default: 50)

    Returns:
        Configured BaseAgent instance

    Example:
        >>> from researcher.llm import AnthropicClient
        >>> llm = AnthropicClient()
        >>> writer = create_writer(llm, "/path/to/workspace")
        >>> result = await writer.run("Write a report on quantum computing")
        >>> print(result.content)  # Summary of document
        >>> print(result.metadata["output_files"])  # Report file path
    """
    # Create workspace manager
    workspace = WorkspaceManager(workspace_dir)

    # Configure tools (no search or analysis - writer works with existing materials)
    tools = [
        ReadTool(workspace),
        WriteTool(workspace),
        EditTool(workspace),
        BashTool(workspace),
        CompleteTool(),
    ]

    # Load system prompt
    prompt_loader = PromptLoader()
    system_prompt = prompt_loader.load("writer")

    # Create and return agent
    return BaseAgent(
        agent_type="writer",
        system_prompt=system_prompt,
        llm_client=llm_client,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
