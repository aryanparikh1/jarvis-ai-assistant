"""
Configuration Manager
=====================
Manages all Jarvis settings stored in config/settings.json.
Provides typed access with defaults and live-reload support.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any

# Project root = two levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# ── Default configuration ────────────────────────────────────────────────────
DEFAULTS: dict[str, Any] = {
    # Appearance
    "theme": "dark",
    "accent_color": "#00D4FF",
    "font_size": 10,
    "opacity": 0.95,
    # Startup
    "start_minimized": False,
    "start_on_boot": False,
    # LLM
    "llm_provider": "openai",          # openai | gemini | ollama
    "openai_model": "gpt-4o-mini",
    "gemini_model": "gemini-2.0-flash",
    "ollama_model": "llama3",
    "ollama_host": "http://localhost:11434",
    "max_tokens": 2048,
    "temperature": 0.7,
    "system_prompt": (
        "You are Jarvis, an advanced AI assistant inspired by Iron Man's JARVIS. "
        "You are highly intelligent, precise, helpful, and occasionally witty. "
        "You assist with computer control, information retrieval, scheduling, and "
        "any task the user needs. Always be concise unless asked for detail."
    ),
    # Voice
    "voice_enabled": True,
    "wake_word": "hey jarvis",
    "wake_word_sensitivity": 0.5,
    "stt_backend": "whisper",          # whisper | google
    "whisper_model": "base",           # tiny | base | small | medium | large
    "tts_backend": "edge",             # edge | pyttsx3
    "tts_voice": "en-US-AriaNeural",
    "tts_rate": "+0%",
    "tts_volume": "+0%",
    "push_to_talk_key": "ctrl+shift+space",
    "vad_threshold": 0.5,
    # Memory
    "memory_enabled": True,
    "memory_max_context": 20,          # messages to include in context
    "auto_extract_memories": True,
    # Permissions
    "permission_safe_auto": True,
    "permission_medium_ask_once": True,
    # API server
    "api_enabled": False,
    "api_host": "127.0.0.1",
    "api_port": 8765,
    # Shortcuts
    "shortcut_show_hide": "ctrl+shift+j",
    "shortcut_push_to_talk": "ctrl+shift+space",
    "shortcut_new_chat": "ctrl+n",
    # Notifications
    "notifications_enabled": True,
    "notification_sound": True,
    # Logging
    "log_level": "INFO",
    "log_to_file": True,
}


class ConfigManager:
    """Thread-safe JSON configuration manager with live-reload."""

    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load settings from disk, merging with defaults."""
        with self._lock:
            if SETTINGS_FILE.exists():
                try:
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                    self._data = {**DEFAULTS, **saved}
                except (json.JSONDecodeError, OSError):
                    self._data = dict(DEFAULTS)
            else:
                self._data = dict(DEFAULTS)
                self._save_unlocked()

    def _save_unlocked(self):
        """Save settings to disk (must hold lock)."""
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._save_unlocked()

    def update(self, values: dict[str, Any]) -> None:
        with self._lock:
            self._data.update(values)
            self._save_unlocked()

    def reset_to_defaults(self) -> None:
        with self._lock:
            self._data = dict(DEFAULTS)
            self._save_unlocked()

    def all(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data)

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        d = PROJECT_ROOT / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def logs_dir(self) -> Path:
        d = PROJECT_ROOT / "logs"
        d.mkdir(exist_ok=True)
        return d


# Singleton
config = ConfigManager()
