"""Agent implementations for the Researcher system.

This module provides specialized agents for different research tasks:
- Searcher: Web search and information gathering
- Analyzer: Deep analysis of collected information
- Writer: Report and document writing
- Orchestrator: Main coordinator agent
"""

from researcher.agents.analyzer import create_analyzer
from researcher.agents.orchestrator import create_orchestrator
from researcher.agents.searcher import create_searcher
from researcher.agents.writer import create_writer

__all__ = [
    "create_searcher",
    "create_analyzer",
    "create_writer",
    "create_orchestrator",
]
