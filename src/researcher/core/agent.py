"""Base Agent implementation for the Researcher system.

This module provides the core Agent abstraction that powers all agents in the system.
"""

from pathlib import Path

from loguru import logger

from researcher.core.tool import Tool, ToolResult
from researcher.core.workspace import WorkspaceManager
from researcher.llm.base import LLMClient, Message


class BaseAgent:
    """Base agent that executes tasks using LLM and tools.

    The agent follows an agentic loop:
    1. Send messages to LLM
    2. LLM responds with text and/or tool calls
    3. Execute requested tools
    4. Add tool results to message history
    5. Repeat until task complete or max steps reached

    Example:
        >>> llm = AnthropicClient(api_key="...")
        >>> tools = [ReadTool(workspace), WriteTool(workspace)]
        >>> agent = BaseAgent(
        ...     agent_type="researcher",
        ...     system_prompt="You are a research assistant.",
        ...     llm_client=llm,
        ...     tools=tools,
        ...     workspace_dir="./workspace",
        ...     max_steps=50
        ... )
        >>> result = await agent.run("Research AI trends in 2025")
    """

    def __init__(
        self,
        agent_type: str,
        system_prompt: str,
        llm_client: LLMClient,
        tools: list[Tool],
        workspace_dir: str | Path,
        max_steps: int = 50,
    ):
        """Initialize the agent.

        Args:
            agent_type: Type identifier for this agent (e.g., "orchestrator", "searcher")
            system_prompt: System prompt defining agent's behavior
            llm_client: LLM client for generating responses
            tools: List of tools available to this agent
            workspace_dir: Workspace directory for file operations
            max_steps: Maximum number of agent steps (default: 50)
        """
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.workspace = WorkspaceManager(workspace_dir)
        self.max_steps = max_steps

        # Message history (starts with system message)
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]

        logger.info(
            f"Initialized {agent_type} agent with {len(tools)} tools, "
            f"workspace={workspace_dir}, max_steps={max_steps}"
        )

    async def run(self, task_description: str) -> ToolResult:
        """Execute a task using the agentic loop.

        The agent will:
        1. Add the task as a user message
        2. Enter the agentic loop (LLM → tools → repeat)
        3. Return when task is complete or max steps reached

        Args:
            task_description: Description of the task to perform

        Returns:
            ToolResult with:
            - success: True if task completed successfully
            - content: Final response or summary
            - metadata: Additional information (steps used, output files, etc.)

        Example:
            >>> result = await agent.run("Read data.txt and summarize it")
            >>> print(result.content)
            "Task completed. Summary: ..."
        """
        logger.info(f"[{self.agent_type}] Starting task: {task_description[:100]}...")

        # Add task as user message
        self.messages.append(Message(role="user", content=task_description))

        step = 0
        output_files = []

        try:
            while step < self.max_steps:
                step += 1
                logger.debug(f"[{self.agent_type}] Step {step}/{self.max_steps}")

                # Get response from LLM
                tool_list = list(self.tools.values())
                response = await self.llm.generate(messages=self.messages, tools=tool_list)

                # Add assistant message to history
                assistant_message = Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls if response.tool_calls else None,
                )
                self.messages.append(assistant_message)

                # Log assistant response
                if response.content:
                    logger.info(f"[{self.agent_type}] Assistant: {response.content[:200]}...")

                # If no tool calls, treat as abnormal termination
                # Agent should explicitly call complete_task to finish
                if not response.tool_calls:
                    logger.warning(
                        f"[{self.agent_type}] Agent stopped without calling complete_task "
                        f"(abnormal termination)"
                    )
                    return ToolResult(
                        success=False,
                        content=response.content,
                        error="Agent did not explicitly complete the task (missing complete_task call)",
                        metadata={
                            "agent_type": self.agent_type,
                            "steps_used": step,
                            "output_files": output_files,
                            "abnormal_termination": True,
                        },
                    )

                # Execute tool calls
                for tool_call in response.tool_calls:
                    function_name = tool_call.function.name
                    arguments = tool_call.function.arguments
                    tool_call_id = tool_call.id

                    logger.info(f"[{self.agent_type}] Calling tool: {function_name}({arguments})")

                    # Execute tool
                    if function_name not in self.tools:
                        tool_result = ToolResult(
                            success=False,
                            error=f"Unknown tool: {function_name}",
                        )
                        logger.error(f"Unknown tool: {function_name}")
                    else:
                        tool = self.tools[function_name]
                        try:
                            tool_result = await tool.execute(**arguments)

                            # Track output files if metadata contains them
                            if tool_result.metadata.get("filepath"):
                                output_files.append(tool_result.metadata["filepath"])

                        except Exception as e:
                            tool_result = ToolResult(
                                success=False,
                                error=f"Tool execution error: {str(e)}",
                            )
                            logger.error(f"Tool {function_name} execution error: {e}")

                    # Log tool result
                    if tool_result.success:
                        logger.info(
                            f"[{self.agent_type}] Tool result: {tool_result.content[:200]}..."
                        )
                    else:
                        logger.warning(f"[{self.agent_type}] Tool error: {tool_result.error}")

                    # Check if this is a complete_task call
                    if function_name == "complete_task":
                        # Task explicitly completed - return the result directly
                        logger.info(
                            f"[{self.agent_type}] Task explicitly completed "
                            f"(success={tool_result.success}) in {step} steps"
                        )
                        # Add metadata about agent execution
                        tool_result.metadata.update(
                            {
                                "agent_type": self.agent_type,
                                "steps_used": step,
                                "output_files": output_files,
                            }
                        )
                        return tool_result

                    # Add tool result to message history
                    tool_message = Message(
                        role="tool",
                        content=(
                            tool_result.content
                            if tool_result.success
                            else f"Error: {tool_result.error}"
                        ),
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    self.messages.append(tool_message)

            # Max steps reached
            logger.warning(f"[{self.agent_type}] Max steps ({self.max_steps}) reached")
            return ToolResult(
                success=False,
                content="",
                error=f"Max steps ({self.max_steps}) reached without completion",
                metadata={
                    "agent_type": self.agent_type,
                    "steps_used": step,
                    "output_files": output_files,
                },
            )

        except Exception as e:
            logger.error(f"[{self.agent_type}] Agent error: {e}")
            return ToolResult(
                success=False,
                error=f"Agent execution error: {str(e)}",
                metadata={
                    "agent_type": self.agent_type,
                    "steps_used": step,
                    "output_files": output_files,
                },
            )

    def reset(self) -> None:
        """Reset the agent's message history.

        Useful when reusing the same agent for multiple tasks.
        """
        self.messages = [Message(role="system", content=self.system_prompt)]
        logger.info(f"[{self.agent_type}] Agent reset")

    def get_message_history(self) -> list[Message]:
        """Get the current message history.

        Returns:
            List of messages in the conversation
        """
        return self.messages.copy()
