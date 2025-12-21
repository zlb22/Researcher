"""Real-time UI visualization for the Researcher CLI.

Provides Claude Code-style visualization showing agent processes,
tool calls, file operations, and workspace state in real-time.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class ResearchUIDisplay:
    """Real-time UI display for research workflow visualization.

    Provides live updates of:
    - Agent activity and decisions
    - Tool calls and results
    - File operations
    - Workspace state
    - Progress tracking
    """

    # Color scheme for different agents (similar to Claude Code)
    AGENT_COLORS = {
        "orchestrator": "bright_blue",
        "searcher": "bright_green",
        "analyzer": "bright_yellow",
        "writer": "bright_magenta",
    }

    TOOL_COLORS = {
        "read_file": "cyan",
        "write_file": "green",
        "edit_file": "yellow",
        "execute_shell": "blue",
        "web_search": "magenta",
        "call_agent": "bright_cyan",
        "complete_task": "bright_green",
    }

    def __init__(self, workspace_dir: str | Path, debug: bool = False):
        """Initialize the UI display.

        Args:
            workspace_dir: Workspace directory path
            debug: Enable debug mode with verbose output
        """
        self.console = Console()
        self.workspace_dir = Path(workspace_dir)
        self.debug = debug

        # Activity log (recent events)
        self.activity_log: list[tuple[str, str, str]] = []  # (timestamp, agent, message)
        self.max_log_entries = 30 if debug else 20  # More entries in debug mode

        # Current agent status
        self.current_agent: str | None = None
        self.current_step: int = 0
        self.total_steps: int = 0

        # File tracking
        self.created_files: set[str] = set()
        self.modified_files: set[str] = set()

        # Progress spinner
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )

        # Live display
        self.live: Live | None = None
        self.layout = Layout()

    def start(self, research_topic: str):
        """Start the live display.

        Args:
            research_topic: Research topic/question
        """
        self.console.clear()

        # Display header
        self._print_header(research_topic)

        # Create layout
        self._create_layout()

        # Start live display
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=4,
            screen=False,
        )
        self.live.start()

    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()
            self.live = None

    def log_agent_start(self, agent_type: str, task: str):
        """Log agent start event.

        Args:
            agent_type: Type of agent (orchestrator/searcher/analyzer/writer)
            task: Task description
        """
        self.current_agent = agent_type
        self.current_step = 0

        timestamp = self._get_timestamp()
        color = self.AGENT_COLORS.get(agent_type, "white")

        message = f"[{color}]▶ {agent_type.upper()}[/{color}]: {task[:80]}..."
        self.activity_log.append((timestamp, agent_type, message))
        self._trim_log()
        self._update_display()

    def log_tool_call(self, agent_type: str, tool_name: str, arguments: dict[str, Any]):
        """Log tool call event.

        Args:
            agent_type: Type of agent making the call
            tool_name: Name of the tool
            arguments: Tool arguments
        """
        self.current_step += 1

        timestamp = self._get_timestamp()
        agent_color = self.AGENT_COLORS.get(agent_type, "white")
        tool_color = self.TOOL_COLORS.get(tool_name, "white")

        # Format arguments (truncate if too long)
        args_str = self._format_arguments(arguments)

        message = (
            f"[{agent_color}]{agent_type}[/{agent_color}] → "
            f"[{tool_color}]{tool_name}[/{tool_color}]: {args_str}"
        )
        self.activity_log.append((timestamp, agent_type, message))
        self._trim_log()
        self._update_display()

    def log_tool_result(self, agent_type: str, tool_name: str, success: bool, content: str = ""):
        """Log tool result event.

        Args:
            agent_type: Type of agent
            tool_name: Name of the tool
            success: Whether tool execution succeeded
            content: Result content (truncated if long in non-debug mode)
        """
        timestamp = self._get_timestamp()
        agent_color = self.AGENT_COLORS.get(agent_type, "white")

        status = "✓" if success else "✗"
        status_color = "green" if success else "red"

        # In debug mode, show more content; otherwise truncate
        if self.debug:
            # Show up to 200 chars in debug mode
            content_preview = content[:200] + "..." if len(content) > 200 else content
        else:
            # Normal mode: 60 chars
            content_preview = content[:60] + "..." if len(content) > 60 else content

        message = (
            f"[{agent_color}]{agent_type}[/{agent_color}] "
            f"[{status_color}]{status}[/{status_color}] "
            f"{tool_name}: {content_preview}"
        )
        self.activity_log.append((timestamp, agent_type, message))
        self._trim_log()
        self._update_display()

    def log_file_operation(self, operation: str, filepath: str):
        """Log file operation event.

        Args:
            operation: Operation type (create/modify/read)
            filepath: File path
        """
        if operation == "create":
            self.created_files.add(filepath)
        elif operation == "modify":
            self.modified_files.add(filepath)

        timestamp = self._get_timestamp()

        operation_color = {"create": "green", "modify": "yellow", "read": "cyan"}.get(
            operation, "white"
        )

        message = f"[{operation_color}]📄 {operation.upper()}[/{operation_color}]: {filepath}"
        self.activity_log.append((timestamp, "file", message))
        self._trim_log()
        self._update_display()

    def log_agent_complete(self, agent_type: str, success: bool, summary: str):
        """Log agent completion event.

        Args:
            agent_type: Type of agent
            success: Whether agent completed successfully
            summary: Completion summary
        """
        timestamp = self._get_timestamp()
        agent_color = self.AGENT_COLORS.get(agent_type, "white")

        status = "✓ COMPLETE" if success else "✗ FAILED"
        status_color = "bright_green" if success else "bright_red"

        summary_preview = summary[:80] + "..." if len(summary) > 80 else summary

        message = (
            f"[{agent_color}]■ {agent_type.upper()}[/{agent_color}] "
            f"[{status_color}]{status}[/{status_color}]: {summary_preview}"
        )
        self.activity_log.append((timestamp, agent_type, message))
        self._trim_log()

        self.current_agent = None
        self.current_step = 0
        self._update_display()

    def print_final_summary(self, success: bool, summary: str, output_files: list[str]):
        """Print final research summary.

        Args:
            success: Whether research completed successfully
            summary: Final summary
            output_files: List of output files
        """
        if self.live:
            self.stop()

        self.console.print()
        self.console.rule("[bold bright_blue]Research Complete[/bold bright_blue]")
        self.console.print()

        # Status
        status_text = (
            "[bold bright_green]✓ SUCCESS[/bold bright_green]"
            if success
            else "[bold bright_red]✗ FAILED[/bold bright_red]"
        )
        self.console.print(f"Status: {status_text}")
        self.console.print()

        # Summary
        summary_panel = Panel(
            summary,
            title="[bold]Summary[/bold]",
            border_style="bright_blue",
        )
        self.console.print(summary_panel)
        self.console.print()

        # Output files
        if output_files:
            self.console.print("[bold bright_cyan]Output Files:[/bold bright_cyan]")
            for filepath in output_files:
                self.console.print(f"  • {filepath}")
            self.console.print()

        # Statistics
        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("Files Created:", str(len(self.created_files)))
        stats_table.add_row("Files Modified:", str(len(self.modified_files)))
        stats_table.add_row("Total Events:", str(len(self.activity_log)))

        stats_panel = Panel(
            stats_table,
            title="[bold]Statistics[/bold]",
            border_style="dim",
        )
        self.console.print(stats_panel)
        self.console.print()

    def print_error(self, error_message: str):
        """Print error message.

        Args:
            error_message: Error message
        """
        if self.live:
            self.stop()

        self.console.print()
        self.console.print(
            Panel(
                error_message,
                title="[bold bright_red]Error[/bold bright_red]",
                border_style="bright_red",
            )
        )
        self.console.print()

    def _print_header(self, research_topic: str):
        """Print header with research topic.

        Args:
            research_topic: Research topic
        """
        self.console.rule("[bold bright_blue]Researcher - Deep Research System[/bold bright_blue]")
        self.console.print()
        self.console.print(f"[bold]Research Topic:[/bold] {research_topic}")
        self.console.print(f"[dim]Workspace:[/dim] {self.workspace_dir}")
        self.console.print()

    def _create_layout(self):
        """Create the layout structure."""
        self.layout.split_column(
            Layout(name="activity", ratio=2),
            Layout(name="status", ratio=1),
        )

    def _update_display(self):
        """Update the live display."""
        if not self.live:
            return

        # Activity log panel
        activity_content = self._render_activity_log()
        self.layout["activity"].update(
            Panel(
                activity_content,
                title="[bold]Activity Log[/bold]",
                border_style="bright_blue",
            )
        )

        # Status panel
        status_content = self._render_status()
        self.layout["status"].update(
            Panel(
                status_content,
                title="[bold]Status[/bold]",
                border_style="cyan",
            )
        )

        self.live.refresh()

    def _render_activity_log(self) -> Group:
        """Render activity log.

        Returns:
            Rich Group with activity log entries
        """
        if not self.activity_log:
            return Group(Text("Waiting for activity...", style="dim"))

        # Show last N entries
        entries = []
        for timestamp, agent, message in self.activity_log[-self.max_log_entries :]:
            entries.append(Text.from_markup(f"[dim]{timestamp}[/dim] {message}"))

        return Group(*entries)

    def _render_status(self) -> Table:
        """Render current status.

        Returns:
            Rich Table with status information
        """
        table = Table(show_header=False, box=None, padding=(0, 1))

        # Current agent
        if self.current_agent:
            agent_color = self.AGENT_COLORS.get(self.current_agent, "white")
            table.add_row(
                "Current Agent:",
                f"[{agent_color}]{self.current_agent.upper()}[/{agent_color}]",
            )
            table.add_row("Step:", f"{self.current_step}")
        else:
            table.add_row("Current Agent:", "[dim]None[/dim]")

        table.add_row("", "")  # Spacer

        # File statistics
        table.add_row("Files Created:", f"[green]{len(self.created_files)}[/green]")
        table.add_row("Files Modified:", f"[yellow]{len(self.modified_files)}[/yellow]")

        return table

    def _format_arguments(self, arguments: dict[str, Any]) -> str:
        """Format tool arguments for display.

        Args:
            arguments: Tool arguments

        Returns:
            Formatted string
        """
        if not arguments:
            return ""

        # Special formatting for common arguments
        parts = []
        for key, value in arguments.items():
            if key == "filepath" or key == "file_path":
                parts.append(f"{Path(value).name}")
            elif key == "command":
                parts.append(f"'{value[:40]}...'")
            elif key == "query":
                parts.append(f"'{value[:40]}...'")
            elif key == "task_description":
                parts.append(f"'{value[:40]}...'")
            elif isinstance(value, str) and len(value) > 40:
                parts.append(f"{key}='{value[:40]}...'")
            else:
                parts.append(f"{key}={value}")

        return ", ".join(parts)

    def _get_timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            Formatted timestamp
        """
        return datetime.now().strftime("%H:%M:%S")

    def _trim_log(self):
        """Trim activity log to max size."""
        if len(self.activity_log) > self.max_log_entries * 2:
            self.activity_log = self.activity_log[-self.max_log_entries :]
