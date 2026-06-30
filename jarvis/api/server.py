"""
FastAPI REST Server — for future mobile app integration
"""

import asyncio
import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.utils.config import config
from jarvis.utils.logger import logger


# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str = "api"

class ChatResponse(BaseModel):
    response: str
    session_id: str

class ToolRequest(BaseModel):
    tool_name: str
    args: dict = {}

class MemoryAddRequest(BaseModel):
    content: str
    memory_type: str = "fact"
    importance: int = 1

class TaskRequest(BaseModel):
    name: str
    trigger_at: str  # ISO datetime
    action: str


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Jarvis AI API",
    description="REST API for Jarvis AI Desktop Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "online", "app": "Jarvis AI Assistant", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to Jarvis and get a response."""
    try:
        from jarvis.core.brain import brain
        response = await brain.get_response(request.message)
        return ChatResponse(response=response, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/execute")
async def execute_tool(request: ToolRequest):
    """Execute a registered Jarvis tool."""
    try:
        from jarvis.tools.registry import registry
        result = registry.execute(request.tool_name, request.args)
        return {"result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List all available tools."""
    from jarvis.tools.registry import registry
    return {"tools": registry.all_schemas()}


@app.post("/memory")
async def add_memory(request: MemoryAddRequest):
    """Add a memory."""
    try:
        from jarvis.memory.memory_manager import memory_manager
        mem_id = memory_manager.add(
            request.content, request.memory_type, request.importance
        )
        return {"id": mem_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/search")
async def search_memory(q: str, n: int = 5):
    """Search memories."""
    try:
        from jarvis.memory.memory_manager import memory_manager
        results = memory_manager.search(q, n)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def status():
    """Get Jarvis system status."""
    from jarvis.utils.config import config
    return {
        "llm_provider": config.get("llm_provider"),
        "voice_enabled": config.get("voice_enabled"),
        "memory_enabled": config.get("memory_enabled"),
    }


# ── Server Runner ─────────────────────────────────────────────────────────────
class APIServer:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None

    def start(self):
        if not config.get("api_enabled", False):
            return
        host = config.get("api_host", "127.0.0.1")
        port = config.get("api_port", 8765)
        self._thread = threading.Thread(
            target=self._run, args=(host, port), daemon=True
        )
        self._thread.start()
        logger.info(f"API server started at http://{host}:{port}")

    def _run(self, host: str, port: int):
        uvicorn_config = uvicorn.Config(
            app, host=host, port=port, log_level="warning"
        )
        self._server = uvicorn.Server(uvicorn_config)
        asyncio.run(self._server.serve())

    def stop(self):
        if self._server:
            self._server.should_exit = True


api_server = APIServer()
