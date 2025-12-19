"""Researcher - A minimal-scaffold deep research system powered by multi-agent collaboration.

This package implements a research system where:
- A main Orchestrator agent coordinates research tasks
- Assistant agents (Searcher, Analyzer, Writer) act as tools
- Agents have maximum freedom to organize information
- Information is stored in files with a "summary + index" pattern for hierarchical access
"""

__version__ = "0.1.0"

from researcher.core import Tool, ToolResult

__all__ = ["Tool", "ToolResult", "__version__"]
