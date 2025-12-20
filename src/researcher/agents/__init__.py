"""Agent implementations for the Researcher system.

This module provides specialized agents for different research tasks:
- Searcher: Web search and information gathering
- Analyzer: Deep analysis of collected information (TODO)
- Writer: Report and document writing (TODO)
- Orchestrator: Main coordinator agent (TODO)
"""

from researcher.agents.searcher import create_searcher

__all__ = ["create_searcher"]
