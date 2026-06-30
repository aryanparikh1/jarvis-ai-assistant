"""Auto-update checker using GitHub releases."""
import httpx
from jarvis.utils.logger import logger

GITHUB_REPO = "aryanparikh415/jarvis-ai-assistant"
CURRENT_VERSION = "1.0.0"

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        resp = httpx.get(url, timeout=10)
        data = resp.json()
        latest = data.get("tag_name", "v1.0.0").lstrip("v")
        from packaging import version
        if version.parse(latest) > version.parse(CURRENT_VERSION):
            return {"available": True, "version": latest, "url": data.get("html_url")}
        return {"available": False, "version": CURRENT_VERSION}
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
        return {"available": False, "error": str(e)}
