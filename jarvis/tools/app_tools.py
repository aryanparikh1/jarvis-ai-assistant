"""
App Tools — Open / Close / Focus Applications
"""

import subprocess
import os
import psutil
import winreg
from jarvis.tools.registry import Tool, registry
from jarvis.utils.logger import logger


# ── Common app paths ─────────────────────────────────────────────────────────
APP_ALIASES = {
    "chrome": ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
               "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"],
    "edge": ["C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"],
    "firefox": ["C:\\Program Files\\Mozilla Firefox\\firefox.exe"],
    "vscode": [os.path.expandvars("%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe")],
    "notepad": ["notepad.exe"],
    "notepad++": ["C:\\Program Files\\Notepad++\\notepad++.exe"],
    "word": [os.path.expandvars("%ProgramFiles%\\Microsoft Office\\root\\Office16\\WINWORD.EXE")],
    "excel": [os.path.expandvars("%ProgramFiles%\\Microsoft Office\\root\\Office16\\EXCEL.EXE")],
    "powerpoint": [os.path.expandvars("%ProgramFiles%\\Microsoft Office\\root\\Office16\\POWERPNT.EXE")],
    "terminal": ["wt.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
    "settings": ["ms-settings:"],
    "control panel": ["control.exe"],
    "spotify": [os.path.expandvars("%APPDATA%\\Spotify\\Spotify.exe")],
    "discord": [os.path.expandvars("%LOCALAPPDATA%\\Discord\\Update.exe --processStart Discord.exe")],
    "slack": [os.path.expandvars("%LOCALAPPDATA%\\slack\\slack.exe")],
}


def open_app(name: str, args: str = "") -> str:
    """Open an application by name or path."""
    name_lower = name.lower().strip()

    # Check aliases
    paths = APP_ALIASES.get(name_lower, [])
    for path in paths:
        if path.startswith("ms-"):
            os.startfile(path)
            return f"Opened {name}"
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            cmd = [expanded] + (args.split() if args else [])
            subprocess.Popen(cmd, shell=False)
            return f"Opened {name}"

    # Try as direct path or system command
    try:
        if os.path.exists(name):
            os.startfile(name)
            return f"Opened {name}"
        subprocess.Popen(name, shell=True)
        return f"Launched: {name}"
    except Exception as e:
        return f"Could not open '{name}': {e}"


def close_app(name: str) -> str:
    """Close all processes matching the given name."""
    name_lower = name.lower()
    killed = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if name_lower in proc.info["name"].lower():
                proc.terminate()
                killed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        return f"Closed: {', '.join(set(killed))}"
    return f"No running process found matching '{name}'"


def list_running_apps() -> str:
    """List all running application windows."""
    apps = set()
    for proc in psutil.process_iter(["name", "status"]):
        try:
            if proc.status() == psutil.STATUS_RUNNING:
                apps.add(proc.name())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return "\n".join(sorted(apps)[:50])


def focus_app(name: str) -> str:
    """Bring an application window to the foreground."""
    try:
        import win32gui
        import win32con

        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if name.lower() in title.lower():
                    results.append(hwnd)

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        if hwnds:
            hwnd = hwnds[0]
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return f"Focused: {win32gui.GetWindowText(hwnd)}"
        return f"Window '{name}' not found"
    except Exception as e:
        return f"Focus error: {e}"


# ── Register tools ────────────────────────────────────────────────────────────
def register_app_tools():
    registry.register(Tool(
        name="open_app",
        description="Open an application by name (e.g. 'Chrome', 'VS Code', 'Notepad')",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "App name or path"},
                "args": {"type": "string", "description": "Optional arguments", "default": ""},
            },
            "required": ["name"]
        },
        handler=open_app,
        action_name="open_app",
    ))

    registry.register(Tool(
        name="close_app",
        description="Close/kill a running application",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Process name to kill"}
            },
            "required": ["name"]
        },
        handler=close_app,
        action_name="close_app",
    ))

    registry.register(Tool(
        name="list_running_apps",
        description="List all currently running applications/processes",
        parameters={"type": "object", "properties": {}},
        handler=list_running_apps,
        action_name="list_directory",
    ))

    registry.register(Tool(
        name="focus_app",
        description="Bring an application window to the foreground",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Window title to focus"}
            },
            "required": ["name"]
        },
        handler=focus_app,
        action_name="open_app",
    ))
