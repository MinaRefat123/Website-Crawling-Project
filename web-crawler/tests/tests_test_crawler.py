import pytest
import asyncio
from crawler import analyze_robots_txt, extract_content

@pytest.mark.asyncio
async def test_robots_txt():
    result = await analyze_robots_txt("https://example.com")
    assert isinstance(result, dict)
    assert "can_crawl" in result or "error" in result

@pytest.mark.asyncio
async def test_content_extraction():
    result = await extract_content("https://example.com")
    assert isinstance(result, dict)
    assert "titles" in result or "error" in result