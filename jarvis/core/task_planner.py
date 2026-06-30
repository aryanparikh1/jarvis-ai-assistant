"""
Task Planner — ReAct-style multi-step planning agent
"""

import json
import asyncio
from typing import AsyncGenerator
from jarvis.core.brain import brain
from jarvis.tools.registry import registry
from jarvis.utils.logger import logger


PLANNER_SYSTEM = """You are Jarvis, an advanced AI assistant with tool access.
When given a task, use the ReAct pattern:
  Thought: reason about what to do
  Action: call a tool
  Observation: interpret the result
  ... repeat until done
  Final Answer: provide the complete response

Available tools are provided as OpenAI function schemas.
Always prefer using tools over guessing. Be efficient and precise."""


class TaskPlanner:
    """
    ReAct-style agentic loop:
    Reason → Act (call tool) → Observe → Repeat → Answer
    """

    def __init__(self, max_iterations: int = 10):
        self._max_iterations = max_iterations

    async def execute(self, task: str) -> AsyncGenerator[str, None]:
        """Run the planning loop and yield status updates + final answer."""
        yield f"🎯 **Task**: {task}\n\n"
        logger.info(f"Task planner started: {task}")

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": task}
        ]

        for iteration in range(self._max_iterations):
            yield f"🔄 **Iteration {iteration + 1}**\n"

            try:
                # Ask LLM what to do
                response = await self._llm_call(messages)

                if not response:
                    yield "⚠️ LLM returned empty response\n"
                    break

                # Check for tool calls
                tool_calls = response.get("tool_calls", [])
                content = response.get("content", "")

                if content:
                    yield f"💭 **Thought**: {content}\n\n"

                if not tool_calls:
                    # Final answer
                    yield f"✅ **Answer**: {content}\n"
                    break

                # Execute each tool call
                messages.append({"role": "assistant", **response})
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    func_args = tc["function"]["arguments"]

                    yield f"🔧 **Action**: `{func_name}({func_args[:100]})`\n"

                    result = registry.execute(func_name, func_args)
                    yield f"👁 **Observation**: {str(result)[:300]}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result),
                    })

            except Exception as e:
                logger.error(f"Planner iteration error: {e}")
                yield f"⚠️ Error: {e}\n"
                break
        else:
            yield "\n⚠️ Max iterations reached. Task may be incomplete.\n"

    async def _llm_call(self, messages: list) -> dict:
        """Call the LLM with tool schemas."""
        import openai
        import keyring
        api_key = keyring.get_password("jarvis", "openai_api_key") or ""
        if not api_key:
            return {"content": "No API key configured. Please add your OpenAI key in Settings."}

        client = openai.AsyncOpenAI(api_key=api_key)
        tools = registry.all_schemas()

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            max_tokens=1024,
        )
        choice = response.choices[0]
        msg = choice.message

        result = {"content": msg.content or ""}
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in msg.tool_calls
            ]
        return result


# Singleton
task_planner = TaskPlanner()
