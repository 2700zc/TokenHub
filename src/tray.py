"""
System tray integration for TokenHub.
Uses pure ctypes (Python standard library) to interact with Windows Shell API.
Zero third-party dependencies.
"""

import ctypes
import threading
import queue
from ctypes import wintypes
from typing import Callable, Optional, Dict

# Windows API constants
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

WM_USER = 0x0400
WM_TRAY_CALLBACK = WM_USER + 1
WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205

IDI_APPLICATION = 32512

# Load Windows DLLs
user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

# Define NOTIFYICONDATAW structure
class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('hWnd', wintypes.HWND),
        ('uID', wintypes.UINT),
        ('uFlags', wintypes.UINT),
        ('uCallbackMessage', wintypes.UINT),
        ('hIcon', wintypes.HICON),
        ('szTip', wintypes.WCHAR * 128),
        ('dwState', wintypes.DWORD),
        ('dwStateMask', wintypes.DWORD),
        ('szInfo', wintypes.WCHAR * 256),
        ('uTimeout', wintypes.UINT),
        ('szInfoTitle', wintypes.WCHAR * 64),
        ('dwInfoFlags', wintypes.DWORD),
    ]

class TrayIcon:
    """System tray icon manager using Windows API via ctypes."""
    
    MENU_SHOW = 1001
    MENU_HIDE = 1002
    MENU_SETTINGS = 1003
    MENU_HELP = 1004
    MENU_EXIT = 1005
    
    def __init__(self, 
                 on_show: Callable,
                 on_hide: Callable,
                 on_settings: Callable,
                 on_help: Callable,
                 on_exit: Callable):
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_settings = on_settings
        self.on_help = on_help
        self.on_exit = on_exit
        
        self._running = False
        self._thread = None
        self._hwnd = None
        self._icon_data = None
        self._command_queue = queue.Queue()
    
    def start(self):
        """Start the tray icon in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_tray_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the tray icon and clean up."""
        self._running = False
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
    
    def _run_tray_loop(self):
        """Run the tray message loop in background thread."""
        # Create a hidden window for receiving messages
        wnd_class = wintypes.WNDCLASSW()
        wnd_class.lpszClassName = "TokenHubTrayClass"
        wnd_class.lpfnWndProc = self._wnd_proc
        
        # Register window class
        if not user32.RegisterClassW(ctypes.byref(wnd_class)):
            # Class might already be registered
            pass
        
        # Create hidden window
        self._hwnd = user32.CreateWindowExW(
            0, "TokenHubTrayClass", "TokenHubTray",
            0, 0, 0, 0, 0, 0, 0, 0, None
        )
        
        if not self._hwnd:
            return
        
        # Create tray icon
        self._create_tray_icon()
        
        # Message loop
        msg = wintypes.MSG()
        while self._running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
            
            # Process commands from queue
            try:
                while True:
                    cmd = self._command_queue.get_nowait()
                    self._process_command(cmd)
            except queue.Empty:
                pass
        
        # Clean up
        self._destroy_tray_icon()
        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None
    
    def _wnd_proc(self, hwnd, msg, wParam, lParam):
        """Window procedure for handling tray messages."""
        if msg == WM_TRAY_CALLBACK:
            # Handle tray icon events
            mouse_msg = lParam
            
            if mouse_msg == WM_RBUTTONUP:
                # Show context menu on right-click
                self._show_menu(hwnd)
            elif mouse_msg == WM_LBUTTONUP:
                # Toggle visibility on left-click
                self._command_queue.put('toggle')
        
        elif msg == WM_COMMAND:
            # Handle menu commands
            menu_id = wParam
            if menu_id == self.MENU_SHOW:
                self._command_queue.put('show')
            elif menu_id == self.MENU_HIDE:
                self._command_queue.put('hide')
            elif menu_id == self.MENU_SETTINGS:
                self._command_queue.put('settings')
            elif menu_id == self.MENU_HELP:
                self._command_queue.put('help')
            elif menu_id == self.MENU_EXIT:
                self._command_queue.put('exit')
        
        elif msg == WM_DESTROY:
            self._running = False
            user32.PostQuitMessage(0)
        
        return user32.DefWindowProcW(hwnd, msg, wParam, lParam)
    
    def _create_tray_icon(self):
        """Create and add the tray icon."""
        icon_data = NOTIFYICONDATAW()
        icon_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        icon_data.hWnd = self._hwnd
        icon_data.uID = 1
        icon_data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        icon_data.uCallbackMessage = WM_TRAY_CALLBACK
        
        # Use default application icon
        icon_data.hIcon = user32.LoadIconW(0, IDI_APPLICATION)
        
        # Tooltip text
        icon_data.szTip = "TokenHub - OpenCode.ai 用量监控"
        
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(icon_data))
        self._icon_data = icon_data
    
    def _destroy_tray_icon(self):
        """Remove the tray icon."""
        if self._icon_data:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._icon_data))
            self._icon_data = None
    
    def _show_menu(self, hwnd):
        """Show the context menu."""
        # Create popup menu
        menu = user32.CreatePopupMenu()
        
        # Add menu items
        user32.AppendMenuW(menu, 0x00000000, self.MENU_SHOW, "显示 TokenHub")
        user32.AppendMenuW(menu, 0x00000000, self.MENU_HIDE, "隐藏 TokenHub")
        user32.AppendMenuW(menu, 0x00000800, 0, None)  # Separator
        user32.AppendMenuW(menu, 0x00000000, self.MENU_SETTINGS, "设置")
        user32.AppendMenuW(menu, 0x00000000, self.MENU_HELP, "帮助")
        user32.AppendMenuW(menu, 0x00000800, 0, None)  # Separator
        user32.AppendMenuW(menu, 0x00000000, self.MENU_EXIT, "退出")
        
        # Get cursor position
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        
        # Ensure window is foreground before showing menu
        user32.SetForegroundWindow(hwnd)
        
        # Show menu
        user32.TrackPopupMenu(
            menu, 0x00000100 | 0x00000008,  # TPM_BOTTOMALIGN | TPM_RIGHTALIGN
            pt.x, pt.y, 0, hwnd, None
        )
        
        # Destroy menu
        user32.DestroyMenu(menu)
    
    def _process_command(self, cmd: str):
        """Process commands from the queue."""
        if cmd == 'show':
            self.on_show()
        elif cmd == 'hide':
            self.on_hide()
        elif cmd == 'toggle':
            # Toggle between show and hide
            self.on_show()  # Simplified: call show (UI handles toggle internally)
        elif cmd == 'settings':
            self.on_settings()
        elif cmd == 'help':
            self.on_help()
        elif cmd == 'exit':
            self.on_exit()