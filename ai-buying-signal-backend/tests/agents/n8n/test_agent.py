import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.n8n.agent import N8nAgent

@pytest.fixture
def agent():
    return N8nAgent()

@pytest.mark.asyncio
async def test_health_check_success(agent, monkeypatch):
    mock_client = MagicMock()
    mock_client.fetch_feed = AsyncMock(return_value="<rss></rss>")
    mock_feed_data = MagicMock()
    mock_feed_data.entries = [{"title": "test"}]
    mock_client.parse_feed.return_value = mock_feed_data
    
    monkeypatch.setattr(agent, "client", mock_client)
    
    assert await agent.health_check() == True

@pytest.mark.asyncio
async def test_health_check_failure(agent, monkeypatch):
    mock_client = MagicMock()
    mock_client.fetch_feed = AsyncMock(side_effect=Exception("HTTP Error"))
    
    monkeypatch.setattr(agent, "client", mock_client)
    
    assert await agent.health_check() == False

@pytest.mark.asyncio
async def test_collect_success(agent, monkeypatch):
    mock_client = MagicMock()
    mock_client.fetch_feed = AsyncMock(return_value="<rss></rss>")
    mock_feed_data = MagicMock()
    mock_feed_data.bozo = False
    mock_feed_data.entries = [
        {"id": "1", "title": "Test 1", "description": "Content 1", "link": "http://test.com/1", "published_parsed": (2026, 8, 24, 12, 0, 0, 0, 0, 0)},
        {"id": "1", "title": "Test 1 Duplicate", "description": "Content 1", "link": "http://test.com/1", "published_parsed": (2026, 8, 24, 12, 0, 0, 0, 0, 0)},
        {"link": "http://test.com/2", "title": "Test 2", "summary": "Content 2", "published_parsed": (2026, 8, 24, 12, 0, 0, 0, 0, 0)}
    ]
    mock_client.parse_feed.return_value = mock_feed_data
    
    monkeypatch.setattr(agent, "client", mock_client)
    
    signals = await agent.collect()
    
    assert len(signals) == 2
    assert signals[0].external_id == "1"
    assert signals[0].title == "Test 1"
    assert signals[1].external_id == "http://test.com/2"
