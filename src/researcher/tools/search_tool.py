"""Web search tools for the Researcher system.

This module provides the TavilySearchTool which allows agents to run
web searches via the Tavily API and receive structured results.
"""

import os
from typing import Any, Sequence

from loguru import logger
from tavily import AsyncTavilyClient

from researcher.core.tool import Tool, ToolResult


class TavilySearchTool(Tool):
    """Tool for performing web searches using the Tavily API.

    Supports configurable result counts and search depth while returning
    concise summaries that agents can act on.

    Environment Variables:
        - TAVILY_API_KEY: API key for Tavily (required unless api_key passed)

    Example:
        >>> search_tool = TavilySearchTool(api_key="tvly-...")
        >>> result = await search_tool.execute(
        ...     query="Latest breakthroughs in quantum computing",
        ...     max_results=5,
        ...     search_depth="advanced",
        ... )
        >>> print(result.content)
    """

    DEFAULT_MAX_RESULTS = 10
    MAX_RESULTS_LIMIT = 20
    DEFAULT_SEARCH_DEPTH = "advanced"
    ALLOWED_DEPTHS: Sequence[str] = ("basic", "advanced")

    def __init__(
        self,
        api_key: str | None = None,
        client: AsyncTavilyClient | None = None,
    ):
        """Initialize the Tavily search tool.

        Args:
            api_key: Tavily API key (optional if client provided or env set)
            client: Preconfigured AsyncTavilyClient (useful for testing)
        """
        if client is not None:
            self.client = client
            return

        if api_key is None:
            api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError(
                "Tavily API key required. Set TAVILY_API_KEY environment variable "
                "or pass api_key when initializing TavilySearchTool."
            )

        self.client = AsyncTavilyClient(api_key=api_key)

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Perform a web search using the Tavily API. Returns a concise summary of the "
            "top findings plus structured metadata with the full JSON response. "
            "Use this to gather fresh information from the internet."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text. Should describe what information is needed.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": self.MAX_RESULTS_LIMIT,
                    "default": self.DEFAULT_MAX_RESULTS,
                    "description": (
                        "Maximum number of search results to return "
                        f"(1-{self.MAX_RESULTS_LIMIT}, default {self.DEFAULT_MAX_RESULTS})."
                    ),
                },
                "search_depth": {
                    "type": "string",
                    "enum": list(self.ALLOWED_DEPTHS),
                    "default": self.DEFAULT_SEARCH_DEPTH,
                    "description": (
                        "Search depth. Use 'basic' for faster but shallower searches, "
                        f"'advanced' for deeper coverage (default {self.DEFAULT_SEARCH_DEPTH})."
                    ),
                },
            },
            "required": ["query"],
        }

    async def execute(
        self,
        query: str,
        max_results: int | None = None,
        search_depth: str | None = None,
    ) -> ToolResult:
        """Execute a Tavily web search."""
        if not query or not query.strip():
            return ToolResult(success=False, error="Query must not be empty")

        if max_results is None:
            max_results = self.DEFAULT_MAX_RESULTS
        elif not (1 <= max_results <= self.MAX_RESULTS_LIMIT):
            return ToolResult(
                success=False,
                error=f"max_results must be between 1 and {self.MAX_RESULTS_LIMIT}",
            )

        if search_depth is None:
            search_depth = self.DEFAULT_SEARCH_DEPTH
        elif search_depth not in self.ALLOWED_DEPTHS:
            return ToolResult(
                success=False,
                error=f"search_depth must be one of {', '.join(self.ALLOWED_DEPTHS)}",
            )

        logger.info(
            f"Running Tavily search: query='{query[:80]}', "
            f"max_results={max_results}, depth={search_depth}"
        )

        try:
            response = await self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
            )
        except Exception as exc:
            logger.error(f"Tavily search failed: {exc}")
            return ToolResult(success=False, error=f"Tavily search failed: {exc}")

        results = response.get("results", [])
        summary = self._build_summary(query, results)

        metadata = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "result_count": len(results),
            "response": response,
        }

        return ToolResult(success=True, content=summary, metadata=metadata)

    def _build_summary(self, query: str, results: list[dict[str, Any]]) -> str:
        """Create a concise textual summary of search findings."""
        if not results:
            return f"No web results found for '{query}'."

        lines = [f"Found {len(results)} results for '{query}'. Top sources:"]
        for result in results[:3]:
            title = result.get("title") or result.get("url", "Unknown source")
            snippet = result.get("content") or result.get("snippet") or ""
            snippet = snippet.strip()
            if len(snippet) > 180:
                snippet = snippet[:177].rstrip() + "..."
            lines.append(f"- {title}: {snippet}")

        return "\n".join(lines)
