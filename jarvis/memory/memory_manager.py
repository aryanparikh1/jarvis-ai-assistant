"""
Memory Manager — Unified long-term memory API
Combines SQLite (structured) + ChromaDB (semantic search).
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from jarvis.utils.config import config
from jarvis.utils.logger import logger


class MemoryManager:
    """
    Unified memory API. Stores in SQLite for structured queries,
    and ChromaDB for semantic similarity search.
    """

    def __init__(self):
        self._db_path = config.data_dir / "jarvis.db"
        self._chroma_dir = config.data_dir / "chroma"
        self._db_conn: sqlite3.Connection | None = None
        self._chroma_collection = None
        self._initialized = False

    def initialize(self):
        """Initialize databases. Call on startup."""
        if self._initialized:
            return
        try:
            self._init_sqlite()
            self._init_chroma()
            self._initialized = True
            logger.info("Memory manager initialized")
        except Exception as e:
            logger.error(f"Memory init error: {e}")

    def _init_sqlite(self):
        self._db_conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._db_conn.row_factory = sqlite3.Row
        self._db_conn.execute("PRAGMA journal_mode=WAL")
        self._db_conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id          TEXT PRIMARY KEY,
                content     TEXT NOT NULL,
                type        TEXT DEFAULT 'fact',
                importance  INTEGER DEFAULT 1,
                tags        TEXT DEFAULT '[]',
                created_at  TEXT,
                updated_at  TEXT,
                metadata    TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                timestamp   TEXT,
                session_id  TEXT
            );

            CREATE TABLE IF NOT EXISTS preferences (
                key         TEXT PRIMARY KEY,
                value       TEXT,
                updated_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                body        TEXT,
                trigger_at  TEXT,
                recurring   TEXT,
                done        INTEGER DEFAULT 0,
                created_at  TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
        """)
        self._db_conn.commit()

    def _init_chroma(self):
        try:
            import chromadb
            self._chroma_dir.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(self._chroma_dir))
            self._chroma_collection = client.get_or_create_collection(
                name="jarvis_memories",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized")
        except ImportError:
            logger.warning("ChromaDB not installed — semantic search disabled")
        except Exception as e:
            logger.error(f"ChromaDB init error: {e}")

    # ── Memory CRUD ───────────────────────────────────────────────────
    def add(
        self, content: str, memory_type: str = "fact",
        importance: int = 1, tags: list[str] = None,
        metadata: dict = None
    ) -> str:
        """Add a memory. Returns the memory ID."""
        if not self._initialized:
            self.initialize()

        mem_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])
        meta_json = json.dumps(metadata or {})

        try:
            self._db_conn.execute(
                "INSERT INTO memories (id,content,type,importance,tags,created_at,updated_at,metadata) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (mem_id, content, memory_type, importance, tags_json, now, now, meta_json)
            )
            self._db_conn.commit()

            # Add to ChromaDB for semantic search
            if self._chroma_collection:
                self._chroma_collection.add(
                    documents=[content],
                    ids=[mem_id],
                    metadatas=[{"type": memory_type, "importance": importance}]
                )
        except Exception as e:
            logger.error(f"Memory add error: {e}")

        return mem_id

    def search(self, query: str, n_results: int = 5,
               memory_type: str = None) -> list[dict]:
        """Semantic search across memories."""
        if not self._initialized:
            self.initialize()

        results = []
        try:
            if self._chroma_collection:
                where = {"type": memory_type} if memory_type else None
                chroma_results = self._chroma_collection.query(
                    query_texts=[query],
                    n_results=min(n_results, max(1, self._chroma_collection.count())),
                    where=where
                )
                ids = chroma_results["ids"][0] if chroma_results["ids"] else []
                for mem_id in ids:
                    row = self._db_conn.execute(
                        "SELECT * FROM memories WHERE id=?", (mem_id,)
                    ).fetchone()
                    if row:
                        results.append(dict(row))
            else:
                # Fallback: SQL LIKE search
                query_pct = f"%{query}%"
                rows = self._db_conn.execute(
                    "SELECT * FROM memories WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
                    (query_pct, n_results)
                ).fetchall()
                results = [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Memory search error: {e}")
        return results

    def get_all(self, limit: int = 200) -> list[dict]:
        """Get all memories."""
        if not self._initialized:
            self.initialize()
        try:
            rows = self._db_conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Memory get_all error: {e}")
            return []

    def delete(self, mem_id: str):
        """Delete a memory by ID."""
        if not self._initialized:
            self.initialize()
        try:
            self._db_conn.execute("DELETE FROM memories WHERE id=?", (mem_id,))
            self._db_conn.commit()
            if self._chroma_collection:
                try:
                    self._chroma_collection.delete(ids=[mem_id])
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Memory delete error: {e}")

    def clear_all(self):
        """Delete all memories."""
        if not self._initialized:
            self.initialize()
        try:
            self._db_conn.execute("DELETE FROM memories")
            self._db_conn.commit()
            if self._chroma_collection:
                try:
                    self._chroma_collection.delete(
                        where={"type": {"$ne": "___nonexistent___"}}
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Memory clear error: {e}")

    # ── Preferences ───────────────────────────────────────────────────
    def set_preference(self, key: str, value: str):
        if not self._initialized:
            self.initialize()
        now = datetime.now().isoformat()
        self._db_conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?,?,?)",
            (key, value, now)
        )
        self._db_conn.commit()

    def get_preference(self, key: str, default: str = "") -> str:
        if not self._initialized:
            self.initialize()
        row = self._db_conn.execute(
            "SELECT value FROM preferences WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else default

    # ── Conversation history ──────────────────────────────────────────
    def save_message(self, role: str, content: str, session_id: str = "default"):
        if not self._initialized:
            self.initialize()
        self._db_conn.execute(
            "INSERT INTO conversations (id,role,content,timestamp,session_id) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), role, content, datetime.now().isoformat(), session_id)
        )
        self._db_conn.commit()

    def get_conversation(self, session_id: str = "default",
                         limit: int = 50) -> list[dict]:
        if not self._initialized:
            self.initialize()
        rows = self._db_conn.execute(
            "SELECT * FROM conversations WHERE session_id=? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ── Context injection ─────────────────────────────────────────────
    def get_context_for_prompt(self, query: str) -> str:
        """Retrieve relevant memories to inject into LLM prompt."""
        if not config.get("memory_enabled", True):
            return ""
        relevant = self.search(query, n_results=3)
        if not relevant:
            return ""
        lines = ["[Relevant Memories]"]
        for mem in relevant:
            lines.append(f"• [{mem.get('type','fact')}] {mem.get('content','')[:200]}")
        return "\n".join(lines)


# Singleton
memory_manager = MemoryManager()
