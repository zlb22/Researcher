"""Orchestrator agent for managing research workflows.

This module provides the Orchestrator agent, which:
- Coordinates research projects with full autonomy
- Calls specialized assistant agents (searcher, analyzer, writer)
- Makes dynamic decisions based on current state
- Supports iterative, non-linear research workflows
"""

from pathlib import Path

from researcher.core.agent import BaseAgent
from researcher.core.workspace import WorkspaceManager
from researcher.llm.base import LLMClient
from researcher.tools.agent_tool import CallAgentTool
from researcher.tools.bash_tool import BashTool
from researcher.tools.control_tools import CompleteTool
from researcher.tools.file_tools import EditTool, ReadTool, WriteTool
from researcher.utils.prompt_loader import PromptLoader


def create_orchestrator(
    llm_client: LLMClient,
    workspace_dir: str | Path,
    max_steps: int = 100,
) -> BaseAgent:
    """Create an Orchestrator agent.

    The Orchestrator agent is the main coordinator that:
    - Manages the overall research workflow
    - Decides when to search, analyze, or write
    - Calls assistant agents based on current needs
    - Adapts dynamically to findings and gaps
    - Supports iterative refinement

    Args:
        llm_client: LLM client for the agent
        workspace_dir: Workspace directory for file operations
        max_steps: Maximum number of agent steps (default: 100, higher than assistants)

    Returns:
        Configured BaseAgent instance

    Example:
        >>> from researcher.llm import AnthropicClient
        >>> llm = AnthropicClient()
        >>> orchestrator = create_orchestrator(llm, "/path/to/workspace")
        >>> result = await orchestrator.run("Research quantum computing applications")
        >>> print(result.content)  # Summary of research
        >>> print(result.metadata["output_files"])  # All generated files
    """
    # Create workspace manager
    workspace = WorkspaceManager(workspace_dir)

    # Configure tools
    # Orchestrator has ALL tools including CallAgentTool
    tools = [
        ReadTool(workspace),
        WriteTool(workspace),
        EditTool(workspace),
        BashTool(workspace),
        CallAgentTool(llm_client, workspace_dir),
        CompleteTool(),
    ]

    # Load system prompt
    prompt_loader = PromptLoader()
    system_prompt = prompt_loader.load("orchestrator")

    # Create and return agent
    # Note: Orchestrator gets more steps than assistant agents
    return BaseAgent(
        agent_type="orchestrator",
        system_prompt=system_prompt,
        llm_client=llm_client,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=max_steps,
    )
