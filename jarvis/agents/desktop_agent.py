"""
Desktop Agent — PyAutoGUI + pywin32 Desktop Automation
"""

import time
import pyautogui
from PySide6.QtCore import QObject, Signal
from jarvis.utils.logger import logger
from jarvis.core.permission_system import permissions

# Safety: don't let PyAutoGUI take over the mouse without fail-safe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class DesktopAgent(QObject):
    """PyAutoGUI + pywin32 desktop automation agent."""

    action_completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def click(self, x: int, y: int, button: str = "left") -> str:
        if not permissions.can_execute("browser_click", f"Click at ({x},{y})"):
            return "Click denied"
        try:
            pyautogui.click(x, y, button=button)
            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Click error: {e}"

    def double_click(self, x: int, y: int) -> str:
        if not permissions.can_execute("browser_click"):
            return "Double-click denied"
        try:
            pyautogui.doubleClick(x, y)
            return f"Double-clicked at ({x}, {y})"
        except Exception as e:
            return f"Error: {e}"

    def right_click(self, x: int, y: int) -> str:
        try:
            pyautogui.click(x, y, button="right")
            return f"Right-clicked at ({x}, {y})"
        except Exception as e:
            return f"Error: {e}"

    def type_text(self, text: str, interval: float = 0.02) -> str:
        try:
            pyautogui.typewrite(text, interval=interval)
            return f"Typed: {text[:50]}"
        except Exception as e:
            return f"Type error: {e}"

    def press_key(self, key: str) -> str:
        try:
            pyautogui.press(key)
            return f"Pressed: {key}"
        except Exception as e:
            return f"Key error: {e}"

    def hotkey(self, *keys) -> str:
        try:
            pyautogui.hotkey(*keys)
            return f"Hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Hotkey error: {e}"

    def scroll(self, clicks: int, x: int = None, y: int = None) -> str:
        try:
            pyautogui.scroll(clicks, x=x, y=y)
            return f"Scrolled {clicks} clicks"
        except Exception as e:
            return f"Scroll error: {e}"

    def get_screen_size(self) -> str:
        w, h = pyautogui.size()
        return f"Screen resolution: {w}x{h}"

    def move_mouse(self, x: int, y: int, duration: float = 0.3) -> str:
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return f"Moved mouse to ({x}, {y})"
        except Exception as e:
            return f"Mouse error: {e}"

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int,
             duration: float = 0.5) -> str:
        try:
            pyautogui.drag(start_x, start_y, end_x - start_x, end_y - start_y,
                           duration=duration, button="left")
            return f"Dragged from ({start_x},{start_y}) to ({end_x},{end_y})"
        except Exception as e:
            return f"Drag error: {e}"

    def locate_on_screen(self, image_path: str) -> str:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if location:
                return f"Found at: {location}"
            return "Image not found on screen"
        except Exception as e:
            return f"Locate error: {e}"


# Singleton
desktop_agent = DesktopAgent()
