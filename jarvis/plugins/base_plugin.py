"""Plugin base class and loader."""
from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Base class for all Jarvis plugins."""

    name: str = "unnamed"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    @abstractmethod
    def on_load(self): ...

    @abstractmethod
    def on_unload(self): ...

    def on_message(self, message: str) -> str | None:
        """Called on every user message. Return a response or None."""
        return None
