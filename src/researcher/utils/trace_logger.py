"""Agent trace logger for framework analysis and improvement.

This module records the complete execution trace of the multi-agent system,
including agent decisions, tool calls, LLM interactions, and resource usage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentTraceLogger:
    """Logger for recording agent execution traces.

    Records all agent activities, tool calls, and decisions to help
    analyze and improve the multi-agent framework.
    """

    def __init__(self, workspace_dir: str | Path, enabled: bool = True):
        """Initialize trace logger.

        Args:
            workspace_dir: Workspace directory
            enabled: Whether tracing is enabled
        """
        self.workspace_dir = Path(workspace_dir)
        self.enabled = enabled
        self.trace_file = self.workspace_dir / "agent_trace.jsonl"
        self.trace_md_file = self.workspace_dir / "agent_trace.md"

        # In-memory trace for current session
        self.trace_events: list[dict[str, Any]] = []
        self.session_start = datetime.now()

        # Statistics
        self.stats = {
            "total_agent_calls": 0,
            "total_tool_calls": 0,
            "total_llm_calls": 0,
            "agents": {},  # Per-agent statistics
            "tools": {},  # Per-tool statistics
        }

        if self.enabled:
            self._write_header()

    def log_agent_start(self, agent_type: str, task: str, parent_agent: str | None = None):
        """Log agent start event.

        Args:
            agent_type: Type of agent (orchestrator/searcher/analyzer/writer)
            task: Task description
            parent_agent: Parent agent if this is a sub-agent call
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "agent_start",
            "agent_type": agent_type,
            "task": task,
            "parent_agent": parent_agent,
        }

        self.trace_events.append(event)
        self._write_event(event)

        # Update stats
        self.stats["total_agent_calls"] += 1
        if agent_type not in self.stats["agents"]:
            self.stats["agents"][agent_type] = {
                "calls": 0,
                "tool_calls": 0,
                "successes": 0,
                "failures": 0,
            }
        self.stats["agents"][agent_type]["calls"] += 1

    def log_agent_complete(self, agent_type: str, success: bool, summary: str, steps_used: int = 0):
        """Log agent completion event.

        Args:
            agent_type: Type of agent
            success: Whether agent completed successfully
            summary: Completion summary
            steps_used: Number of steps used
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "agent_complete",
            "agent_type": agent_type,
            "success": success,
            "summary": summary,
            "steps_used": steps_used,
        }

        self.trace_events.append(event)
        self._write_event(event)

        # Update stats
        if success:
            self.stats["agents"][agent_type]["successes"] += 1
        else:
            self.stats["agents"][agent_type]["failures"] += 1

    def log_tool_call(self, agent_type: str, tool_name: str, arguments: dict[str, Any]):
        """Log tool call event.

        Args:
            agent_type: Agent making the call
            tool_name: Name of the tool
            arguments: Tool arguments
        """
        if not self.enabled:
            return

        # Truncate long arguments for readability
        truncated_args = {}
        for key, value in arguments.items():
            if isinstance(value, str) and len(value) > 100:
                truncated_args[key] = value[:100] + "..."
            else:
                truncated_args[key] = value

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "tool_call",
            "agent_type": agent_type,
            "tool_name": tool_name,
            "arguments": truncated_args,
        }

        self.trace_events.append(event)
        self._write_event(event)

        # Update stats
        self.stats["total_tool_calls"] += 1
        self.stats["agents"][agent_type]["tool_calls"] += 1

        if tool_name not in self.stats["tools"]:
            self.stats["tools"][tool_name] = {"calls": 0, "successes": 0, "failures": 0}
        self.stats["tools"][tool_name]["calls"] += 1

    def log_tool_result(self, agent_type: str, tool_name: str, success: bool, content: str = ""):
        """Log tool result event.

        Args:
            agent_type: Agent that called the tool
            tool_name: Name of the tool
            success: Whether tool execution succeeded
            content: Result content (truncated)
        """
        if not self.enabled:
            return

        # Truncate content
        truncated_content = content[:200] + "..." if len(content) > 200 else content

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "tool_result",
            "agent_type": agent_type,
            "tool_name": tool_name,
            "success": success,
            "content": truncated_content,
        }

        self.trace_events.append(event)
        self._write_event(event)

        # Update stats
        if success:
            self.stats["tools"][tool_name]["successes"] += 1
        else:
            self.stats["tools"][tool_name]["failures"] += 1

    def log_llm_call(
        self,
        agent_type: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Log LLM API call.

        Args:
            agent_type: Agent making the call
            model: Model name
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
        """
        if not self.enabled:
            return

        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "llm_call",
            "agent_type": agent_type,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

        self.trace_events.append(event)
        self._write_event(event)

        # Update stats
        self.stats["total_llm_calls"] += 1

    def finalize(self):
        """Finalize trace and write summary.

        Writes statistics and markdown summary.
        """
        if not self.enabled:
            return

        # Calculate session duration
        duration = (datetime.now() - self.session_start).total_seconds()

        # Write final statistics
        stats_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "session_complete",
            "duration_seconds": duration,
            "statistics": self.stats,
        }
        self._write_event(stats_event)

        # Write markdown summary
        self._write_markdown_summary(duration)

    def _write_header(self):
        """Write trace file header."""
        # JSONL file - no header needed, just ensure file exists
        self.trace_file.touch()

        # Markdown file header
        with open(self.trace_md_file, "w") as f:
            f.write("# Agent Trace Log\n\n")
            f.write(f"Session started: {self.session_start.isoformat()}\n\n")
            f.write("---\n\n")

    def _write_event(self, event: dict[str, Any]):
        """Write event to JSONL file.

        Args:
            event: Event dictionary
        """
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _write_markdown_summary(self, duration: float):
        """Write human-readable markdown summary.

        Args:
            duration: Session duration in seconds
        """
        with open(self.trace_md_file, "a") as f:
            f.write("\n\n## Session Summary\n\n")
            f.write(f"- **Duration**: {duration:.2f} seconds\n")
            f.write(f"- **Total Agent Calls**: {self.stats['total_agent_calls']}\n")
            f.write(f"- **Total Tool Calls**: {self.stats['total_tool_calls']}\n")
            f.write(f"- **Total LLM Calls**: {self.stats['total_llm_calls']}\n\n")

            # Agent statistics
            f.write("### Agent Statistics\n\n")
            f.write("| Agent | Calls | Tools | Success | Failure |\n")
            f.write("|-------|-------|-------|---------|----------|\n")
            for agent_type, stats in self.stats["agents"].items():
                f.write(
                    f"| {agent_type} | {stats['calls']} | {stats['tool_calls']} | "
                    f"{stats['successes']} | {stats['failures']} |\n"
                )
            f.write("\n")

            # Tool statistics
            f.write("### Tool Statistics\n\n")
            f.write("| Tool | Calls | Success | Failure | Success Rate |\n")
            f.write("|------|-------|---------|---------|-------------|\n")
            for tool_name, stats in self.stats["tools"].items():
                total = stats["calls"]
                success_rate = (stats["successes"] / total * 100) if total > 0 else 0
                f.write(
                    f"| {tool_name} | {total} | {stats['successes']} | "
                    f"{stats['failures']} | {success_rate:.1f}% |\n"
                )
            f.write("\n")

            # Event timeline
            f.write("### Event Timeline\n\n")
            for event in self.trace_events:
                timestamp = event["timestamp"].split("T")[1].split(".")[0]
                event_type = event["event_type"]

                if event_type == "agent_start":
                    f.write(
                        f"- **{timestamp}** - 🚀 `{event['agent_type']}` started: "
                        f"{event['task'][:80]}...\n"
                    )
                elif event_type == "agent_complete":
                    status = "✅" if event["success"] else "❌"
                    f.write(
                        f"- **{timestamp}** - {status} `{event['agent_type']}` "
                        f"completed ({event.get('steps_used', 0)} steps)\n"
                    )
                elif event_type == "tool_call":
                    f.write(
                        f"  - **{timestamp}** - 🔧 `{event['agent_type']}` → "
                        f"`{event['tool_name']}`\n"
                    )
                elif event_type == "tool_result":
                    status = "✓" if event["success"] else "✗"
                    f.write(
                        f"  - **{timestamp}** - {status} `{event['tool_name']}`: "
                        f"{event['content'][:60]}...\n"
                    )
                elif event_type == "llm_call":
                    f.write(
                        f"  - **{timestamp}** - 🤖 LLM call ({event['model']}): "
                        f"{event['input_tokens']}→{event['output_tokens']} tokens\n"
                    )

            f.write("\n---\n\n")
            f.write(f"Session ended: {datetime.now().isoformat()}\n")
