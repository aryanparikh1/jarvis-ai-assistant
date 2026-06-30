"""Tool Executor — dispatches tool calls from the LLM."""
from jarvis.tools.registry import registry
from jarvis.utils.logger import logger

class ToolExecutor:
    def execute(self, tool_name: str, args: dict):
        return registry.execute(tool_name, args)
    def register_all_tools(self):
        from jarvis.tools.app_tools import register_app_tools
        from jarvis.tools.file_tools import register_file_tools
        from jarvis.tools.system_tools import register_system_tools
        from jarvis.tools.web_tools import register_web_tools
        register_app_tools()
        register_file_tools()
        register_system_tools()
        register_web_tools()
        logger.info("All tools registered")

tool_executor = ToolExecutor()
