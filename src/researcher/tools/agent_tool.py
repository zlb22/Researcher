"""Agent calling tools for the Researcher system.

This module provides the CallAgentTool which allows agents to invoke
other specialized agents (searcher, analyzer, writer) as tools.
"""

from pathlib import Path
from typing import Any, Literal

from loguru import logger

from researcher.core.tool import Tool, ToolResult
from researcher.llm.base import LLMClient


class CallAgentTool(Tool):
    """Tool for calling specialized assistant agents.

    This implements the "agent-as-tool" pattern, allowing a main agent
    (orchestrator) to delegate tasks to specialized assistant agents.

    The tool creates and runs assistant agents on-demand, returning their
    results as ToolResult objects with summaries and file references.

    Example:
        >>> llm = AnthropicClient()
        >>> call_agent = CallAgentTool(llm, "/path/to/workspace")
        >>> result = await call_agent.execute(
        ...     agent_type="searcher",
        ...     task_description="Search for AI breakthroughs in 2024"
        ... )
        >>> print(result.content)  # Agent's summary
        >>> print(result.metadata["output_files"])  # Files created
    """

    def __init__(
        self,
        llm_client: LLMClient,
        workspace_dir: str | Path,
    ):
        """Initialize the CallAgentTool.

        Args:
            llm_client: LLM client to use for assistant agents
            workspace_dir: Workspace directory for file operations
        """
        self.llm_client = llm_client
        self.workspace_dir = Path(workspace_dir)

    @property
    def name(self) -> str:
        """Tool name."""
        return "call_agent"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Call a specialized assistant agent to perform a specific task. "
            "Available agents: "
            "'searcher' (web search and information gathering), "
            "'analyzer' (deep analysis of information), "
            "'writer' (report and document writing). "
            "The agent will work autonomously and return a summary plus "
            "file paths where detailed results are saved."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "enum": ["searcher", "analyzer", "writer"],
                    "description": (
                        "Type of agent to call. "
                        "'searcher': Search web and gather information. "
                        "'analyzer': Analyze collected data and extract insights. "
                        "'writer': Write reports and documents."
                    ),
                },
                "task_description": {
                    "type": "string",
                    "description": (
                        "Clear description of the task for the agent. "
                        "Be specific about what you want the agent to do."
                    ),
                },
                "context_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": (
                        "Optional list of file paths the agent should read "
                        "for context (relative to workspace)."
                    ),
                },
                "max_steps": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 50,
                    "description": "Maximum number of steps the agent can take (default: 50).",
                },
            },
            "required": ["agent_type", "task_description"],
        }

    async def execute(
        self,
        agent_type: Literal["searcher", "analyzer", "writer"],
        task_description: str,
        context_files: list[str] | None = None,
        max_steps: int = 50,
    ) -> ToolResult:
        """Execute an assistant agent.

        Args:
            agent_type: Type of agent ("searcher", "analyzer", "writer")
            task_description: Task for the agent to perform
            context_files: Optional list of files for agent context
            max_steps: Maximum number of agent steps

        Returns:
            ToolResult with:
            - success: Whether agent completed successfully
            - content: Agent's summary
            - metadata: {
                "agent_type": str,
                "output_files": list[str],
                "steps_used": int,
                ...
            }
        """
        if not task_description or not task_description.strip():
            return ToolResult(
                success=False,
                error="task_description must not be empty",
            )

        if context_files is None:
            context_files = []

        logger.info(f"Calling {agent_type} agent: {task_description[:100]}...")

        # Create agent
        try:
            agent = self._create_agent(agent_type, max_steps)
        except Exception as e:
            logger.error(f"Failed to create {agent_type} agent: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to create {agent_type} agent: {str(e)}",
                metadata={"agent_type": agent_type},
            )

        # Build full task description with context
        full_task = task_description
        if context_files:
            file_list = ", ".join(context_files)
            full_task = (
                f"{task_description}\n\n"
                f"Context files to review: {file_list}\n"
                f"Read these files first to understand the existing work."
            )

        # Setup UI integration for sub-agent if UI is available
        ui = getattr(self, "_ui", None)
        trace_logger = getattr(self, "_trace_logger", None)

        if ui:
            self._setup_subagent_ui(agent, ui, trace_logger)
            # Log sub-agent start
            ui.log_agent_start(agent_type, task_description)

        if trace_logger:
            # Log sub-agent start with parent context
            trace_logger.log_agent_start(agent_type, task_description, parent_agent="orchestrator")

        # Run agent
        try:
            result = await agent.run(full_task)
            logger.info(
                f"{agent_type} agent completed (success={result.success}, "
                f"steps={result.metadata.get('steps_used', '?')})"
            )

            # Log sub-agent completion
            if ui:
                ui.log_agent_complete(agent_type, result.success, result.content)
            if trace_logger:
                steps_used = result.metadata.get("steps_used", 0)
                trace_logger.log_agent_complete(
                    agent_type, result.success, result.content, steps_used
                )

            return result
        except Exception as e:
            logger.error(f"{agent_type} agent failed with exception: {e}")

            # Log sub-agent failure
            if ui:
                ui.log_agent_complete(agent_type, False, f"Exception: {str(e)}")
            if trace_logger:
                trace_logger.log_agent_complete(agent_type, False, f"Exception: {str(e)}", 0)

            return ToolResult(
                success=False,
                error=f"Agent execution failed: {str(e)}",
                metadata={
                    "agent_type": agent_type,
                    "exception": str(e),
                },
            )

    def _setup_subagent_ui(self, agent: Any, ui: Any, trace_logger: Any = None):
        """Setup UI integration for a sub-agent.

        Args:
            agent: Sub-agent instance
            ui: UI display instance
            trace_logger: Optional trace logger instance
        """
        # Wrap all tool execute methods for UI and trace logging
        for tool in agent.tools.values():
            # Skip if already wrapped
            if hasattr(tool, "_ui_wrapped"):
                continue

            original_execute = tool.execute

            def make_execute_with_ui(orig_exec, tool_name, agent_type):
                """Create wrapped execute function with UI and trace logging."""

                async def execute_with_ui(**kwargs):
                    # Log tool call
                    if ui:
                        ui.log_tool_call(agent_type, tool_name, kwargs)
                    if trace_logger:
                        trace_logger.log_tool_call(agent_type, tool_name, kwargs)

                    # Execute tool
                    try:
                        result = await orig_exec(**kwargs)

                        # Log tool result - use error field if content is empty and failed
                        display_content = result.content
                        if not result.success and not display_content and result.error:
                            display_content = f"Error: {result.error}"

                        if ui:
                            ui.log_tool_result(
                                agent_type, tool_name, result.success, display_content
                            )

                            # Track file operations
                            if tool_name == "write_file" and result.success:
                                filepath = kwargs.get("filepath", "")
                                ui.log_file_operation("create", filepath)
                            elif tool_name == "edit_file" and result.success:
                                filepath = kwargs.get("filepath", "")
                                ui.log_file_operation("modify", filepath)

                        if trace_logger:
                            trace_logger.log_tool_result(
                                agent_type, tool_name, result.success, display_content
                            )

                        return result
                    except Exception as e:
                        error_msg = f"Exception: {str(e)}"
                        if ui:
                            ui.log_tool_result(agent_type, tool_name, False, error_msg)
                        if trace_logger:
                            trace_logger.log_tool_result(agent_type, tool_name, False, error_msg)
                        raise

                return execute_with_ui

            # Create and set wrapped execute
            tool.execute = make_execute_with_ui(original_execute, tool.name, agent.agent_type)
            tool._ui_wrapped = True

    def _create_agent(
        self,
        agent_type: Literal["searcher", "analyzer", "writer"],
        max_steps: int,
    ) -> Any:  # Returns BaseAgent
        """Create an assistant agent instance.

        Args:
            agent_type: Type of agent to create
            max_steps: Maximum steps for the agent

        Returns:
            Configured BaseAgent instance

        Raises:
            ValueError: If agent_type is unknown
        """
        if agent_type == "searcher":
            from researcher.agents.searcher import create_searcher

            return create_searcher(
                llm_client=self.llm_client,
                workspace_dir=self.workspace_dir,
                max_steps=max_steps,
            )
        elif agent_type == "analyzer":
            from researcher.agents.analyzer import create_analyzer

            return create_analyzer(
                llm_client=self.llm_client,
                workspace_dir=self.workspace_dir,
                max_steps=max_steps,
            )
        elif agent_type == "writer":
            from researcher.agents.writer import create_writer

            return create_writer(
                llm_client=self.llm_client,
                workspace_dir=self.workspace_dir,
                max_steps=max_steps,
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
