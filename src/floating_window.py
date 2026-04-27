"""
Floating window UI for TokenHub - Compact Toolbar Style.
Small rounded corners (4px), acrylic glass, no title bar.
Uses WM_NCCALCSIZE to hide title bar while keeping DWM effects.
"""

import tkinter as tk
import ctypes
from ctypes import wintypes
from typing import Callable, Dict, Any
import math
import time as time_module

# Windows API Constants
WM_NCCALCSIZE = 0x0083
GWL_WNDPROC = -4

WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUNDSMALL = 3

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ('AccentState', ctypes.c_uint),
        ('AccentFlags', ctypes.c_uint),
        ('GradientColor', ctypes.c_uint),
        ('AnimationId', ctypes.c_uint)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ('Attribute', ctypes.c_int),
        ('Data', ctypes.POINTER(ACCENT_POLICY)),
        ('SizeOfData', ctypes.c_size_t)
    ]


class FloatingWindow:
    """Compact toolbar with acrylic glass and small rounded corners."""
    
    WINDOW_WIDTH = 720
    EXPANDED_HEIGHT = 58
    COLLAPSED_HEIGHT = 3
    CORNER_RADIUS = 8
    ANIM_DURATION = 180
    TRIGGER_ZONE = 12
    HIDE_DELAY = 200
    
    ICONS = {'rolling': '📈', 'weekly': '📅', 'monthly': '🕐'}
    LABELS = {'rolling': '滚动用量', 'weekly': '每周用量', 'monthly': '每月用量'}
    
    def __init__(self, root: tk.Tk, theme_colors: dict,
                 on_settings: Callable, on_help: Callable, on_exit: Callable,
                 on_refresh: Callable = None):
        self.root = root
        self.on_settings = on_settings
        self.on_help = on_help
        self.on_exit = on_exit
        self.on_refresh = on_refresh
        
        self._is_docked = True
        self._is_visible = True
        self._animating = False
        self._hide_timer = None
        self._dragging = False
        self._normal_y = 8
        self._hidden_y = -self.EXPANDED_HEIGHT + self.COLLAPSED_HEIGHT
        
        # Create borderless window (NO title bar at all)
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)  # Remove title bar completely
        self.window.attributes('-topmost', True)
        
        # Position
        sw = self.window.winfo_screenwidth()
        self._x = (sw - self.WINDOW_WIDTH) // 2
        self.window.geometry(
            f"{self.WINDOW_WIDTH}x{self.EXPANDED_HEIGHT}+{self._x}+{self._normal_y}")
        
        # Apply DWM effects after window exists
        self.window.after(10, self._setup_window_effects)
        
        # Colors
        self.text_color = '#2c3e50'
        self.accent_color = '#1976d2'
        self.subtitle_color = '#7f8c8d'
        
        # Build UI
        self._build_ui()
        
        # Events
        self.window.bind('<Button-1>', self._on_press)
        self.window.bind('<B1-Motion>', self._on_drag)
        self.window.bind('<ButtonRelease-1>', self._on_release)
        self.window.bind('<Button-3>', lambda e: self._show_menu(e))
        self.window.bind('<Enter>', self._on_enter)
        
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # Hover refresh cooldown (avoid frequent refresh when mouse jittering)
        self._last_refresh_time = 0
        self._refresh_cooldown = 5  # seconds
        
        # Monitor
        self._schedule_check()
    
    def _setup_window_effects(self):
        """Setup acrylic glass and hide title bar."""
        try:
            hwnd = self.window.winfo_id()
            user32 = ctypes.windll.user32
            dwmapi = ctypes.windll.dwmapi
            
            # 1. Acrylic effect - Windows 11 style
            accent = ACCENT_POLICY()
            accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent.AccentFlags = 2
            # ABGR format: rgba(255,255,255,0.7) = 0xB3FFFFFF
            accent.GradientColor = 0xB3FFFFFF
            
            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = WCA_ACCENT_POLICY
            data.Data = ctypes.pointer(accent)
            data.SizeOfData = ctypes.sizeof(accent)
            
            user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
            
            # 2. Small rounded corners (Windows 11 DWM)
            corner_val = ctypes.c_int(DWMWCP_ROUNDSMALL)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(corner_val),
                ctypes.sizeof(corner_val)
            )
            
            # 3. Fallback: CreateRoundRectRgn for all Windows versions
            self._set_window_rgn(hwnd)
            
            # 3. Hide title bar via WM_NCCALCSIZE
            self._setup_title_bar_removal(hwnd)
            
        except Exception:
            pass
    
    def _set_window_rgn(self, hwnd):
        """Set window region to rounded rectangle for all Windows versions."""
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            
            w = self.WINDOW_WIDTH
            h = self.EXPANDED_HEIGHT
            r = self.CORNER_RADIUS * 2  # CreateRoundRectRgn uses diameter
            
            # Create rounded rectangle region
            region = gdi32.CreateRoundRectRgn(0, 0, w, h, r, r)
            
            # Apply to window
            user32.SetWindowRgn(hwnd, region, True)
        except Exception:
            pass
    
    def _setup_title_bar_removal(self, hwnd):
        """Remove title bar while keeping DWM frame."""
        user32 = ctypes.windll.user32
        self._orig_wndproc = user32.GetWindowLongW(hwnd, GWL_WNDPROC)
        
        def wnd_proc(hwnd, msg, wParam, lParam):
            if msg == WM_NCCALCSIZE and wParam:
                return 0
            return user32.CallWindowProcW(
                ctypes.c_void_p(self._orig_wndproc),
                hwnd, msg, wParam, lParam
            )
        
        self._wndproc_callback = ctypes.WINFUNCTYPE(
            wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )(wnd_proc)
        
        user32.SetWindowLongW(
            hwnd, GWL_WNDPROC,
            ctypes.cast(self._wndproc_callback, ctypes.c_void_p).value
        )
        
        SWP_FRAMECHANGED = 0x0020
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                           SWP_FRAMECHANGED | 0x0002 | 0x0001 | 0x0004 | 0x0200 | 0x0040)
    
    def _build_ui(self):
        """Build compact toolbar UI with reset time."""
        # Semi-transparent content for glass effect
        self.content = tk.Frame(self.window, bg='#ffffff')
        self.content.place(x=0, y=0, relwidth=1, relheight=1)
        
        inner = tk.Frame(self.content, bg='#ffffff')
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        
        self.sections = {}
        names = ['rolling', 'weekly', 'monthly']
        
        for i, name in enumerate(names):
            sec_frame = tk.Frame(inner, bg='#ffffff')
            sec_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Row 1: icon + label + percent
            row1 = tk.Frame(sec_frame, bg='#ffffff')
            row1.pack()
            
            tk.Label(row1, text=self.ICONS[name], font=('Segoe UI Emoji', 13),
                    bg='#ffffff', fg=self.subtitle_color).pack(side=tk.LEFT, padx=(0, 5))
            
            tk.Label(row1, text=self.LABELS[name], font=('Microsoft YaHei', 10),
                    bg='#ffffff', fg=self.text_color).pack(side=tk.LEFT, padx=(0, 6))
            
            pct = tk.Label(row1, text='--', font=('Microsoft YaHei', 12, 'bold'),
                          bg='#ffffff', fg=self.accent_color)
            pct.pack(side=tk.LEFT)
            
            # Row 2: reset time
            reset_lbl = tk.Label(sec_frame, text='距离重置: --', font=('Microsoft YaHei', 8),
                                bg='#ffffff', fg=self.subtitle_color)
            reset_lbl.pack(pady=(2, 0))
            
            if i < 2:
                sep = tk.Frame(inner, bg='#e0e0e0', width=1)
                sep.pack(side=tk.LEFT, fill=tk.Y, pady=8)
            
            self.sections[name] = {'percent': pct, 'reset': reset_lbl}
        
        self.context_menu = tk.Menu(self.window, tearoff=0, bg='#ffffff', fg=self.text_color)
        self.context_menu.add_command(label='设置', command=self.on_settings)
        self.context_menu.add_command(label='帮助', command=self.on_help)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='退出', command=self.on_exit)
    
    # Auto-hide
    def _schedule_check(self):
        self.window.after(100, self._check_and_schedule)
    
    def _check_and_schedule(self):
        self._check_auto_hide()
        self._schedule_check()
    
    def _check_auto_hide(self):
        if self._animating or self._dragging:
            return
        
        my = self.window.winfo_pointery()
        cy = self.window.winfo_y()
        is_at_top = cy < 20 or self._is_docked
        
        if is_at_top:
            self._is_docked = True
            if my < self.TRIGGER_ZONE:
                if not self._is_visible:
                    self._animate_show()
                if self._hide_timer:
                    self.window.after_cancel(self._hide_timer)
                    self._hide_timer = None
            else:
                wx1 = self.window.winfo_x()
                wx2 = wx1 + self.WINDOW_WIDTH
                wy1 = self.window.winfo_y()
                wy2 = wy1 + (self.EXPANDED_HEIGHT if self._is_visible else self.COLLAPSED_HEIGHT)
                inside = wx1 <= self.window.winfo_pointerx() <= wx2 and wy1 <= my <= wy2
                
                if not inside and self._is_visible and not self._hide_timer:
                    self._hide_timer = self.window.after(self.HIDE_DELAY, self._do_hide)
        else:
            self._is_docked = False
            if not self._is_visible:
                self._animate_show()
    
    def _do_hide(self):
        self._hide_timer = None
        if self._is_docked and self._is_visible:
            self._animate_hide()
    
    # Animation
    def _animate_hide(self):
        if self._animating:
            return
        self._animating = True
        self._is_visible = False
        self._run_animation(self._normal_y, self._hidden_y)
    
    def _animate_show(self):
        if self._animating:
            return
        self._animating = True
        self._is_visible = True
        self._run_animation(self._hidden_y, self._normal_y)
    
    def _run_animation(self, start_y, end_y):
        start_time = time_module.time()
        duration = self.ANIM_DURATION / 1000.0
        
        def step():
            elapsed = time_module.time() - start_time
            t = min(elapsed / duration, 1.0)
            ease = 1 - math.pow(1 - t, 3)
            current_y = int(start_y + (end_y - start_y) * ease)
            self.window.geometry(f'+{self._x}+{current_y}')
            if t < 1.0:
                self.window.after(16, step)
            else:
                self._animating = False
        
        step()
    
    # Hover refresh
    def _on_enter(self, event):
        """Trigger data refresh when mouse enters the floating window."""
        if self.on_refresh and not self._dragging:
            now = time_module.time()
            if now - self._last_refresh_time >= self._refresh_cooldown:
                self._last_refresh_time = now
                self.on_refresh()
    
    # Drag
    def _on_press(self, event):
        self._drag_start_x = event.x_root - self.window.winfo_x()
        self._drag_start_y = event.y_root - self.window.winfo_y()
        self._dragging = True
        if self._hide_timer:
            self.window.after_cancel(self._hide_timer)
            self._hide_timer = None
    
    def _on_drag(self, event):
        if not self._dragging:
            return
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self._x = x
        self._normal_y = y
        self.window.geometry(f'+{x}+{y}')
        self._is_docked = False
        if not self._is_visible:
            self._is_visible = True
    
    def _on_release(self, event):
        self._dragging = False
    
    def _show_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)
    
    # Data
    def update_data(self, data: Dict[str, Any]):
        if 'error' in data:
            for name in ['rolling', 'weekly', 'monthly']:
                self.sections[name]['percent'].configure(text='--')
                self.sections[name]['reset'].configure(text='距离重置: --')
            return
        
        mapping = {'rolling': 'rollingUsage', 'weekly': 'weeklyUsage', 'monthly': 'monthlyUsage'}
        for section_name, api_key in mapping.items():
            usage = data.get(api_key, {})
            percent = usage.get('percent')
            reset_time = usage.get('reset_time', '--')
            
            text = f"{percent}%" if percent is not None else "--"
            self.sections[section_name]['percent'].configure(text=text)
            self.sections[section_name]['reset'].configure(text=f'距离重置: {reset_time}')
    
    def show(self):
        self.window.deiconify()
        if not self._is_visible:
            self._animate_show()
    
    def hide(self):
        self.window.withdraw()
    
    def destroy(self):
        self.window.destroy()
