import pytest

from researcher.tools.search_tool import TavilySearchTool


class FakeTavilyClient:
    def __init__(self, response: dict | None = None, should_raise: bool = False):
        self.response = response or {
            "results": [
                {
                    "title": "AI Advances 2024",
                    "url": "https://example.com/ai",
                    "content": "Overview of the latest AI advances in 2024.",
                },
                {
                    "title": "Research Trends",
                    "url": "https://example.com/trends",
                    "content": "Key research trends summarized.",
                },
            ],
            "answer": "Summary goes here.",
        }
        self.should_raise = should_raise
        self.calls = []

    async def search(self, **kwargs):
        self.calls.append(kwargs)
        if self.should_raise:
            raise RuntimeError("network error")
        return self.response


@pytest.mark.asyncio
async def test_tavily_search_tool_success():
    fake_client = FakeTavilyClient()
    tool = TavilySearchTool(client=fake_client)

    result = await tool.execute(query="ai breakthroughs")

    assert result.success is True
    assert "Found 2 results" in result.content
    assert result.metadata["result_count"] == 2
    assert result.metadata["response"] == fake_client.response

    call_args = fake_client.calls[0]
    assert call_args["query"] == "ai breakthroughs"
    assert call_args["max_results"] == tool.DEFAULT_MAX_RESULTS
    assert call_args["search_depth"] == tool.DEFAULT_SEARCH_DEPTH


@pytest.mark.asyncio
async def test_tavily_search_tool_handles_errors():
    fake_client = FakeTavilyClient(should_raise=True)
    tool = TavilySearchTool(client=fake_client)

    result = await tool.execute(query="ai breakthroughs", max_results=5)

    assert result.success is False
    assert "Tavily search failed" in result.error


def test_tavily_search_tool_requires_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with pytest.raises(ValueError):
        TavilySearchTool()


@pytest.mark.asyncio
async def test_tavily_search_tool_validates_inputs():
    fake_client = FakeTavilyClient()
    tool = TavilySearchTool(client=fake_client)

    result = await tool.execute(query="", max_results=0)
    assert result.success is False
    assert "Query must not be empty" in result.error

    result = await tool.execute(query="ai", max_results=100)
    assert result.success is False
    assert "max_results" in result.error

    result = await tool.execute(query="ai", search_depth="deep")
    assert result.success is False
    assert "search_depth" in result.error
