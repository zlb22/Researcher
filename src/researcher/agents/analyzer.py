"""Analyzer agent for deep analysis and insight extraction.

This module provides the Analyzer agent, which specializes in:
- Reading and understanding collected data
- Identifying patterns and trends
- Extracting meaningful insights
- Documenting analysis with clear conclusions
"""

from pathlib import Path

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm.base import LLMClient
from researcher.tools.bash_tool import BashTool
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.utils.prompt_loader import PromptLoader


def create_analyzer(
    llm_client: LLMClient,
    workspace_dir: str | Path,
    max_steps: int = 50,
) -> BaseAgent:
    """Create an Analyzer agent.

    The Analyzer agent is responsible for:
    - Deep analysis of collected information
    - Pattern and trend identification
    - Insight extraction and documentation
    - Identifying data gaps and limitations

    Args:
        llm_client: LLM client for the agent
        workspace_dir: Workspace directory for file operations
        max_steps: Maximum number of agent steps (default: 50)

    Returns:
        Configured BaseAgent instance

    Example:
        >>> from researcher.llm import AnthropicClient
        >>> llm = AnthropicClient()
        >>> analyzer = create_analyzer(llm, "/path/to/workspace")
        >>> result = await analyzer.run("Analyze quantum computing trends")
        >>> print(result.content)  # Summary of analysis
        >>> print(result.metadata["output_files"])  # Analysis files
    """
    # Create workspace manager
    workspace = WorkspaceManager(workspace_dir)

    # Configure tools (no search tool - analyzer works with existing data)
    tools = [
        ReadTool(workspace),
        WriteTool(workspace),
        EditTool(workspace),
        BashTool(workspace),
        CompleteTool(),
    ]

    # Load system prompt
    prompt_loader = PromptLoader()
    system_prompt = prompt_loader.load("analyzer")

    # Create and return agent
    return BaseAgent(
        agent_type="analyzer",
        system_prompt=system_prompt,
        llm_client=llm_client,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
