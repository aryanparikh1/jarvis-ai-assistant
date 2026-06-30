"""
Web Tools — Search, Summarize, Fetch Webpages
"""

import httpx
import json
from jarvis.tools.registry import Tool, registry
from jarvis.utils.logger import logger


def search_web(query: str, engine: str = "duckduckgo", num_results: int = 5) -> str:
    """Search the web and return top results."""
    try:
        if engine == "duckduckgo":
            return _ddg_search(query, num_results)
        else:
            return _ddg_search(query, num_results)
    except Exception as e:
        return f"Search error: {e}"


def _ddg_search(query: str, num_results: int = 5) -> str:
    """DuckDuckGo Instant Answer API."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()

        results = []
        if data.get("AbstractText"):
            results.append(f"**Summary**: {data['AbstractText'][:500]}")
        if data.get("AbstractURL"):
            results.append(f"**Source**: {data['AbstractURL']}")

        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append(f"• {topic['Text'][:200]}")

        return "\n".join(results) if results else f"No results found for: {query}"
    except Exception as e:
        return f"DuckDuckGo search error: {e}"


def fetch_webpage(url: str, summarize: bool = True) -> str:
    """Fetch and optionally summarize a webpage."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return f"Non-HTML content ({content_type}), cannot summarize"

        # Extract readable text
        text = _extract_text(response.text)

        if summarize and len(text) > 500:
            # Truncate for LLM context
            return f"**Page content from {url}**:\n\n{text[:3000]}" + (
                "\n\n[... content truncated ...]" if len(text) > 3000 else ""
            )
        return text
    except Exception as e:
        return f"Fetch error for '{url}': {e}"


def _extract_text(html: str) -> str:
    """Extract readable text from HTML."""
    try:
        from readability import Document
        from bs4 import BeautifulSoup
        doc = Document(html)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception:
        return html[:2000]


def get_weather(location: str) -> str:
    """Get current weather for a location using wttr.in."""
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = httpx.get(url, timeout=10)
        data = response.json()
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        area_name = area["areaName"][0]["value"]
        country = area["country"][0]["value"]
        temp_c = current["temp_C"]
        temp_f = current["temp_F"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind_kmph = current["windspeedKmph"]
        feels_c = current["FeelsLikeC"]
        return (
            f"Weather in {area_name}, {country}:\n"
            f"• Condition: {desc}\n"
            f"• Temperature: {temp_c}°C / {temp_f}°F (feels like {feels_c}°C)\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind: {wind_kmph} km/h"
        )
    except Exception as e:
        return f"Weather fetch error: {e}"


def register_web_tools():
    registry.register(Tool("search_web", "Search the web for information",
        {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "default": 5},
        }, "required": ["query"]}, search_web, "search_web"))
    registry.register(Tool("fetch_webpage", "Fetch and read a webpage",
        {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
            "summarize": {"type": "boolean", "default": True},
        }, "required": ["url"]}, fetch_webpage, "web_summarize"))
    registry.register(Tool("get_weather", "Get current weather for a location",
        {"type": "object", "properties": {
            "location": {"type": "string", "description": "City name or coordinates"}
        }, "required": ["location"]}, get_weather, "get_weather"))
