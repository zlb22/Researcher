"""Searcher agent for web search and information gathering.

This module provides the Searcher agent, which specializes in:
- Executing web searches using Tavily
- Evaluating and refining search queries
- Organizing search results into structured files
- Providing concise summaries of findings
"""

from pathlib import Path

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm.base import LLMClient
from researcher.tools.bash_tool import BashTool
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.tools.search_tool import TavilySearchTool
from researcher.utils.prompt_loader import PromptLoader


def create_searcher(
    llm_client: LLMClient,
    workspace_dir: str | Path,
    max_steps: int = 50,
) -> BaseAgent:
    """Create a Searcher agent.

    The Searcher agent is responsible for:
    - Executing web searches to gather information
    - Organizing search results into files
    - Providing structured summaries of findings

    Args:
        llm_client: LLM client for the agent
        workspace_dir: Workspace directory for file operations
        max_steps: Maximum number of agent steps (default: 50)

    Returns:
        Configured BaseAgent instance

    Example:
        >>> from researcher.llm import AnthropicClient
        >>> llm = AnthropicClient()
        >>> searcher = create_searcher(llm, "/path/to/workspace")
        >>> result = await searcher.run("Search for AI breakthroughs in 2024")
        >>> print(result.content)  # Summary
        >>> print(result.metadata["output_files"])  # List of created files
    """
    # Create workspace manager
    workspace = WorkspaceManager(workspace_dir)

    # Configure tools
    tools = [
        TavilySearchTool(),
        ReadTool(workspace),
        WriteTool(workspace),
        EditTool(workspace),
        BashTool(workspace),
        CompleteTool(),
    ]

    # Load system prompt
    prompt_loader = PromptLoader()
    system_prompt = prompt_loader.load("searcher")

    # Create and return agent
    return BaseAgent(
        agent_type="searcher",
        system_prompt=system_prompt,
        llm_client=llm_client,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
