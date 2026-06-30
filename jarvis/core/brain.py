"""
LLM Brain — Core AI Engine
============================
Supports OpenAI, Google Gemini, and Ollama backends.
Handles conversation history, tool-calling, and streaming responses.
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

from jarvis.utils.config import config
from jarvis.utils.logger import logger


class Message:
    """A single conversation message."""
    def __init__(self, role: str, content: str):
        self.role = role    # "user" | "assistant" | "system" | "tool"
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class LLMBrain:
    """
    Unified LLM interface supporting OpenAI, Gemini, and Ollama.
    Manages conversation history and provides streaming responses.
    """

    def __init__(self):
        self._history: list[Message] = []
        self._tools: list[dict] = []
        self._provider = config.get("llm_provider", "openai")
        self._openai_client = None
        self._gemini_model = None

    # ── Initialization ────────────────────────────────────────────────
    def _get_openai_client(self):
        if self._openai_client is None:
            try:
                import openai
                import keyring
                api_key = keyring.get_password("jarvis", "openai_api_key")
                if not api_key:
                    # Fall back to config
                    api_key = config.get("openai_api_key", "")
                self._openai_client = openai.AsyncOpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to init OpenAI client: {e}")
                raise
        return self._openai_client

    def _get_gemini_model(self):
        if self._gemini_model is None:
            try:
                import google.generativeai as genai
                import keyring
                api_key = keyring.get_password("jarvis", "gemini_api_key")
                if not api_key:
                    api_key = config.get("gemini_api_key", "")
                genai.configure(api_key=api_key)
                model_name = config.get("gemini_model", "gemini-2.0-flash")
                self._gemini_model = genai.GenerativeModel(
                    model_name,
                    system_instruction=self._system_prompt()
                )
            except Exception as e:
                logger.error(f"Failed to init Gemini model: {e}")
                raise
        return self._gemini_model

    def _system_prompt(self) -> str:
        return config.get(
            "system_prompt",
            "You are Jarvis, an advanced AI assistant. Be helpful, precise, and concise."
        )

    # ── History management ────────────────────────────────────────────
    def add_message(self, role: str, content: str):
        self._history.append(Message(role, content))
        # Trim to max context
        max_ctx = config.get("memory_max_context", 20)
        if len(self._history) > max_ctx:
            self._history = self._history[-max_ctx:]

    def clear_history(self):
        self._history.clear()

    def get_history(self) -> list[dict]:
        return [m.to_dict() for m in self._history]

    # ── Tool registration ─────────────────────────────────────────────
    def register_tools(self, tools: list[dict]):
        """Register OpenAI-format tool schemas."""
        self._tools = tools

    # ── Main inference ────────────────────────────────────────────────
    async def stream_response(
        self, user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response token-by-token.
        Yields text chunks as they arrive.
        """
        self.add_message("user", user_message)
        provider = config.get("llm_provider", "openai")

        try:
            if provider == "openai":
                async for chunk in self._stream_openai():
                    yield chunk
            elif provider == "gemini":
                async for chunk in self._stream_gemini():
                    yield chunk
            elif provider == "ollama":
                async for chunk in self._stream_ollama():
                    yield chunk
            else:
                yield f"[Error] Unknown provider: {provider}"
        except Exception as e:
            logger.error(f"LLM error: {e}")
            yield f"\n\n⚠️ Error: {str(e)}"

    async def _stream_openai(self) -> AsyncGenerator[str, None]:
        client = self._get_openai_client()
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(self.get_history())
        model = config.get("openai_model", "gpt-4o-mini")

        full_response = ""
        kwargs = dict(
            model=model,
            messages=messages,
            max_tokens=config.get("max_tokens", 2048),
            temperature=config.get("temperature", 0.7),
            stream=True,
        )
        if self._tools:
            kwargs["tools"] = self._tools
            kwargs["tool_choice"] = "auto"

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_response += delta.content
                    yield delta.content

        self.add_message("assistant", full_response)

    async def _stream_gemini(self) -> AsyncGenerator[str, None]:
        model = self._get_gemini_model()
        # Build Gemini history (user/model alternation)
        history = []
        for msg in self._history[:-1]:  # All but the latest user msg
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})

        chat = model.start_chat(history=history)
        user_msg = self._history[-1].content if self._history else ""

        full_response = ""
        response = await asyncio.to_thread(
            lambda: chat.send_message(user_msg, stream=True)
        )
        for chunk in response:
            text = chunk.text
            if text:
                full_response += text
                yield text
                await asyncio.sleep(0)

        self.add_message("assistant", full_response)

    async def _stream_ollama(self) -> AsyncGenerator[str, None]:
        import ollama
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(self.get_history())
        model_name = config.get("ollama_model", "llama3")

        full_response = ""
        stream = await asyncio.to_thread(
            lambda: ollama.chat(
                model=model_name,
                messages=messages,
                stream=True,
                options={
                    "num_predict": config.get("max_tokens", 2048),
                    "temperature": config.get("temperature", 0.7),
                }
            )
        )
        for chunk in stream:
            text = chunk["message"]["content"]
            if text:
                full_response += text
                yield text
                await asyncio.sleep(0)

        self.add_message("assistant", full_response)

    async def get_response(self, user_message: str) -> str:
        """Non-streaming response (convenience wrapper)."""
        chunks = []
        async for chunk in self.stream_response(user_message):
            chunks.append(chunk)
        return "".join(chunks)

    def switch_provider(self, provider: str):
        """Hot-switch LLM provider."""
        config.set("llm_provider", provider)
        self._openai_client = None
        self._gemini_model = None
        logger.info(f"Switched LLM provider to: {provider}")


# Singleton
brain = LLMBrain()
