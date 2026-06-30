"""
Windows Startup Registration
=============================
Registers/unregisters Jarvis to run on Windows startup via the registry.
"""

import sys
import os
import winreg
from jarvis.utils.logger import logger

STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JarvisAI"


def register_startup() -> bool:
    """Add Jarvis to Windows startup registry."""
    try:
        exe_path = sys.executable
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        )
        # If packaged as .exe, use sys.executable directly
        if getattr(sys, "frozen", False):
            cmd = f'"{exe_path}"'
        else:
            cmd = f'"{exe_path}" "{script_path}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_KEY,
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        logger.info(f"Registered startup: {cmd}")
        return True
    except Exception as e:
        logger.error(f"Failed to register startup: {e}")
        return False


def unregister_startup() -> bool:
    """Remove Jarvis from Windows startup registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_KEY,
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        logger.info("Unregistered startup")
        return True
    except FileNotFoundError:
        return True  # Already not registered
    except Exception as e:
        logger.error(f"Failed to unregister startup: {e}")
        return False


def is_registered() -> bool:
    """Check if Jarvis is registered to start on boot."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_KEY,
            0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False
