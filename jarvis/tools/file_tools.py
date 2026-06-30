"""
File Tools — Create, Read, Update, Delete, Search Files
"""

import os
import shutil
import glob
import json
from pathlib import Path
from datetime import datetime

from jarvis.tools.registry import Tool, registry
from jarvis.utils.logger import logger


def read_file(path: str) -> str:
    """Read and return file contents."""
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 4000:
            return content[:4000] + f"\n... [truncated, {len(content)} chars total]"
        return content
    except Exception as e:
        return f"Error reading '{path}': {e}"


def write_file(path: str, content: str, mode: str = "w") -> str:
    """Write or append content to a file."""
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        return f"Written to '{path}' ({len(content)} chars)"
    except Exception as e:
        return f"Error writing '{path}': {e}"


def create_file(path: str, content: str = "") -> str:
    return write_file(path, content, mode="w")


def append_file(path: str, content: str) -> str:
    return write_file(path, content + "\n", mode="a")


def delete_file(path: str) -> str:
    """Delete a file."""
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file: {path}"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return f"Deleted folder: {path}"
        return f"Path not found: {path}"
    except Exception as e:
        return f"Error deleting '{path}': {e}"


def list_directory(path: str = ".") -> str:
    """List files in a directory."""
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        items = os.listdir(path)
        result = []
        for item in sorted(items)[:100]:
            full = os.path.join(path, item)
            if os.path.isdir(full):
                result.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full)
                result.append(f"📄 {item} ({size:,} bytes)")
        return f"Contents of {path}:\n" + "\n".join(result)
    except Exception as e:
        return f"Error listing '{path}': {e}"


def search_files(query: str, directory: str = "~", extension: str = "") -> str:
    """Search for files matching a pattern."""
    try:
        directory = os.path.expandvars(os.path.expanduser(directory))
        ext = f"*{extension}" if extension else "*"
        pattern = f"**/*{query}*{extension}" if query else f"**/{ext}"
        matches = []
        for match in Path(directory).glob(pattern):
            matches.append(str(match))
            if len(matches) >= 20:
                break
        if not matches:
            return f"No files found matching '{query}' in {directory}"
        return "Found:\n" + "\n".join(matches)
    except Exception as e:
        return f"Search error: {e}"


def move_file(src: str, dst: str) -> str:
    """Move or rename a file."""
    try:
        src = os.path.expandvars(os.path.expanduser(src))
        dst = os.path.expandvars(os.path.expanduser(dst))
        shutil.move(src, dst)
        return f"Moved '{src}' → '{dst}'"
    except Exception as e:
        return f"Error moving: {e}"


def get_file_info(path: str) -> str:
    """Get metadata about a file."""
    try:
        path = os.path.expandvars(os.path.expanduser(path))
        stat = os.stat(path)
        return json.dumps({
            "path": path,
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_dir": os.path.isdir(path),
        }, indent=2)
    except Exception as e:
        return f"Error getting info for '{path}': {e}"


def register_file_tools():
    registry.register(Tool("read_file", "Read file contents",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        read_file, "read_file"))
    registry.register(Tool("write_file", "Write content to a file",
        {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"},
            "mode": {"type": "string", "enum": ["w", "a"], "default": "w"}
        }, "required": ["path", "content"]},
        write_file, "write_file"))
    registry.register(Tool("create_file", "Create a new file",
        {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string", "default": ""}
        }, "required": ["path"]},
        create_file, "create_file"))
    registry.register(Tool("delete_file", "Delete a file or folder",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        delete_file, "delete_file"))
    registry.register(Tool("list_directory", "List files in a directory",
        {"type": "object", "properties": {"path": {"type": "string", "default": "."}},
         "required": []},
        list_directory, "list_directory"))
    registry.register(Tool("search_files", "Search for files by name",
        {"type": "object", "properties": {
            "query": {"type": "string"},
            "directory": {"type": "string", "default": "~"},
            "extension": {"type": "string", "default": ""},
        }, "required": ["query"]},
        search_files, "list_directory"))
    registry.register(Tool("move_file", "Move or rename a file",
        {"type": "object", "properties": {
            "src": {"type": "string"}, "dst": {"type": "string"}
        }, "required": ["src", "dst"]},
        move_file, "move_file"))
    registry.register(Tool("get_file_info", "Get file metadata",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        get_file_info, "read_file"))
