"""
Plugin Loader — Dynamic plugin loading from the /plugins directory.
"""

import os
import importlib.util
import sys
from pathlib import Path

from jarvis.plugins.base_plugin import BasePlugin
from jarvis.utils.logger import logger


class PluginLoader:
    """Loads and manages Jarvis plugins."""

    def __init__(self, plugin_dir: str = "plugins"):
        self._plugin_dir = Path(plugin_dir)
        self._plugins: dict[str, BasePlugin] = {}

    def load_all(self):
        """Load all .py plugins from the plugins directory."""
        if not self._plugin_dir.exists():
            return

        for file in self._plugin_dir.glob("*.py"):
            if file.stem.startswith("_"):
                continue
            try:
                self._load_plugin(file)
            except Exception as e:
                logger.error(f"Failed to load plugin {file.name}: {e}")

    def _load_plugin(self, path: Path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)

        # Find plugin class
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and issubclass(obj, BasePlugin)
                    and obj is not BasePlugin):
                plugin = obj()
                plugin.on_load()
                self._plugins[plugin.name] = plugin
                logger.info(f"Plugin loaded: {plugin.name} v{plugin.version}")

    def unload_all(self):
        for plugin in self._plugins.values():
            try:
                plugin.on_unload()
            except Exception as e:
                logger.error(f"Plugin unload error [{plugin.name}]: {e}")
        self._plugins.clear()

    def process_message(self, message: str) -> str | None:
        """Let plugins process a message. First non-None response wins."""
        for plugin in self._plugins.values():
            try:
                result = plugin.on_message(message)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Plugin message error [{plugin.name}]: {e}")
        return None

    @property
    def loaded_plugins(self) -> list[dict]:
        return [
            {"name": p.name, "description": p.description, "version": p.version}
            for p in self._plugins.values()
        ]


plugin_loader = PluginLoader()
