"""
System Tools — Volume, Brightness, WiFi, System Info
"""

import os
import subprocess
import platform
import psutil
import json
from datetime import datetime

from jarvis.tools.registry import Tool, registry
from jarvis.utils.logger import logger


def get_system_info() -> str:
    """Get comprehensive system information."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()
    info = {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_usage_pct": cpu,
        "ram_total_gb": round(ram.total / 1e9, 2),
        "ram_used_pct": ram.percent,
        "disk_total_gb": round(disk.total / 1e9, 2),
        "disk_used_pct": disk.percent,
        "battery_pct": battery.percent if battery else "N/A",
        "battery_plugged": battery.power_plugged if battery else "N/A",
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return json.dumps(info, indent=2)


def get_volume() -> str:
    """Get current system volume level (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        level = int(volume.GetMasterVolumeLevelScalar() * 100)
        return f"Current volume: {level}%"
    except Exception as e:
        return f"Could not get volume: {e}"


def set_volume(level: int) -> str:
    """Set system volume (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        level = max(0, min(100, level))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Could not set volume: {e}"


def get_brightness() -> str:
    """Get current screen brightness."""
    try:
        import screen_brightness_control as sbc
        brightness = sbc.get_brightness(display=0)
        return f"Current brightness: {brightness[0]}%"
    except Exception as e:
        return f"Could not get brightness: {e}"


def set_brightness(level: int) -> str:
    """Set screen brightness (0-100)."""
    try:
        import screen_brightness_control as sbc
        level = max(0, min(100, level))
        sbc.set_brightness(level, display=0)
        return f"Brightness set to {level}%"
    except Exception as e:
        return f"Could not set brightness: {e}"


def run_terminal_command(command: str, shell: bool = True) -> str:
    """Execute a terminal command and return output."""
    try:
        result = subprocess.run(
            command, shell=shell, capture_output=True,
            text=True, timeout=30, encoding="utf-8", errors="replace"
        )
        output = result.stdout or result.stderr or "(no output)"
        if len(output) > 3000:
            output = output[:3000] + "\n... [truncated]"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command error: {e}"


def take_screenshot(filename: str = "") -> str:
    """Take a screenshot and save it."""
    try:
        import pyautogui
        from datetime import datetime
        if not filename:
            filename = os.path.join(
                os.path.expanduser("~/Desktop"),
                f"jarvis_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
        pyautogui.screenshot(filename)
        return f"Screenshot saved: {filename}"
    except Exception as e:
        return f"Screenshot error: {e}"


def get_clipboard() -> str:
    """Get clipboard content."""
    try:
        import pyperclip
        return pyperclip.paste() or "(clipboard is empty)"
    except Exception as e:
        return f"Clipboard error: {e}"


def set_clipboard(text: str) -> str:
    """Set clipboard content."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Copied to clipboard ({len(text)} chars)"
    except Exception as e:
        return f"Clipboard error: {e}"


def lock_screen() -> str:
    """Lock the Windows screen."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked"
    except Exception as e:
        return f"Lock error: {e}"


def get_current_time() -> str:
    """Get current date and time."""
    return datetime.now().strftime("Today is %A, %B %d, %Y. Time: %H:%M:%S")


def register_system_tools():
    registry.register(Tool("get_system_info", "Get system info (CPU, RAM, disk, battery)",
        {"type": "object", "properties": {}}, get_system_info, "get_time"))
    registry.register(Tool("get_volume", "Get system volume level",
        {"type": "object", "properties": {}}, get_volume, "get_volume"))
    registry.register(Tool("set_volume", "Set system volume (0-100)",
        {"type": "object", "properties": {
            "level": {"type": "integer", "minimum": 0, "maximum": 100}
        }, "required": ["level"]}, set_volume, "set_volume"))
    registry.register(Tool("get_brightness", "Get screen brightness",
        {"type": "object", "properties": {}}, get_brightness, "get_brightness"))
    registry.register(Tool("set_brightness", "Set screen brightness (0-100)",
        {"type": "object", "properties": {
            "level": {"type": "integer", "minimum": 0, "maximum": 100}
        }, "required": ["level"]}, set_brightness, "set_brightness"))
    registry.register(Tool("run_terminal_command", "Execute a terminal/shell command",
        {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to execute"}
        }, "required": ["command"]}, run_terminal_command, "run_terminal_command"))
    registry.register(Tool("take_screenshot", "Take a screenshot",
        {"type": "object", "properties": {
            "filename": {"type": "string", "default": ""}
        }}, take_screenshot, "screenshot"))
    registry.register(Tool("get_clipboard", "Read clipboard content",
        {"type": "object", "properties": {}}, get_clipboard, "read_clipboard"))
    registry.register(Tool("set_clipboard", "Copy text to clipboard",
        {"type": "object", "properties": {
            "text": {"type": "string"}
        }, "required": ["text"]}, set_clipboard, "write_clipboard"))
    registry.register(Tool("lock_screen", "Lock the Windows screen",
        {"type": "object", "properties": {}}, lock_screen, "close_app"))
    registry.register(Tool("get_current_time", "Get current date and time",
        {"type": "object", "properties": {}}, get_current_time, "get_time"))
