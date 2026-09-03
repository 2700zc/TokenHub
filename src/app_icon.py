"""
Application icon loader.
Loads the exe icon resource for the tray icon and window title bar icons.
"""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_DEFAULTSIZE = 0x0040
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1


def _load_icon(size: int):
    """Load the application icon of the given size from the exe resources."""
    try:
        hinst = kernel32.GetModuleHandleW(None)
        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
            ctypes.c_int, ctypes.c_int, wintypes.UINT
        ]
        user32.LoadImageW.restype = wintypes.HANDLE
        # PyInstaller embeds the icon under resource IDs 0/1/2; try each.
        for resid in (0, 1, 2):
            name = ctypes.cast(ctypes.c_void_p(resid), ctypes.c_wchar_p)
            icon = user32.LoadImageW(hinst, name, IMAGE_ICON, size, size, LR_DEFAULTSIZE)
            if icon:
                return icon
    except Exception:
        pass
    try:
        return user32.LoadIconW(0, IDI_APPLICATION)
    except Exception:
        return None


def get_app_icon(size: int = 32):
    """Return an HICON handle for the application icon."""
    return _load_icon(size)


def set_window_icon(hwnd, icon):
    """Set the icon on a Tk window's title bar / taskbar entry."""
    if not icon or not hwnd:
        return
    try:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, icon)
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, icon)
    except Exception:
        pass