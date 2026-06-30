"""
Tool Registry
==============
Central registry for all Jarvis tools.
Tools are registered as OpenAI function-call schemas and dispatched here.
"""

import json
from typing import Callable, Any
from jarvis.utils.logger import logger
from jarvis.core.permission_system import permissions


class Tool:
    def __init__(
        self, name: str, description: str, parameters: dict,
        handler: Callable, action_name: str = None
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.action_name = action_name or name

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, args: dict | str) -> Any:
        """Execute a tool by name with permission check."""
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}

        # Permission check
        description = f"Jarvis wants to: {tool.description}"
        if not permissions.can_execute(tool.action_name, description):
            return f"Action '{name}' was denied by permission system."

        try:
            result = tool.handler(**args)
            logger.info(f"Tool executed: {name}({args}) → {str(result)[:100]}")
            return result
        except Exception as e:
            logger.error(f"Tool error [{name}]: {e}")
            return f"Error executing {name}: {str(e)}"


# Global registry
registry = ToolRegistry()
