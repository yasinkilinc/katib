"""
UI Automation Tools using PyAutoGUI
WARNING: These tools take control of the mouse and keyboard.
"""
import pyautogui
import time
from typing import Dict, Any

# Fail-safe: moving mouse to corner throws exception
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # Add delay between actions

def ui_click(x: int = None, y: int = None, clicks: int = 1, button: str = 'left') -> Dict[str, Any]:
    """Click at coordinates or current position"""
    try:
        current_x, current_y = pyautogui.position()
        target_x = x if x is not None else current_x
        target_y = y if y is not None else current_y
        
        pyautogui.click(x=target_x, y=target_y, clicks=clicks, button=button)
        return {"success": True, "message": f"Clicked at ({target_x}, {target_y})"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ui_type(text: str, interval: float = 0.05) -> Dict[str, Any]:
    """Type text"""
    try:
        pyautogui.write(text, interval=interval)
        return {"success": True, "message": f"Typed: {text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ui_press_key(key: str, modifiers: list = None) -> Dict[str, Any]:
    """Press a key with optional modifiers"""
    try:
        if modifiers:
            # e.g. ['command', 'shift']
            with pyautogui.hold(modifiers[0]):
                 # Basic support for one modifier for now, or use hotkey
                 if len(modifiers) > 1:
                     # Complex hotkey
                     pyautogui.hotkey(*modifiers, key)
                 else:
                     pyautogui.press(key)
        else:
            pyautogui.press(key)
            
        return {"success": True, "message": f"Pressed {key}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ui_scroll(clicks: int) -> Dict[str, Any]:
    """Scroll up or down"""
    try:
        pyautogui.scroll(clicks)
        return {"success": True, "message": f"Scrolled {clicks}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def ui_get_position() -> Dict[str, Any]:
    """Get current mouse position"""
    x, y = pyautogui.position()
    return {"success": True, "x": x, "y": y}
