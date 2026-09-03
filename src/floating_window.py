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
    
    COLUMN_WIDTH = 240
    EXPANDED_HEIGHT = 58
    COLLAPSED_SIZE = 3    # visible strip when hidden (any edge)
    CORNER_RADIUS = 8
    ANIM_DURATION = 180
    TRIGGER_ZONE = 12
    HIDE_DELAY = 200
    EDGE_THRESHOLD = 20   # distance from screen edge to trigger docking
    
    ICONS = {'rolling': '📈', 'weekly': '📅', 'monthly': '🕐', 'deepseek': '💰'}
    LABELS = {'rolling': '滚动用量', 'weekly': '每周用量', 'monthly': '每月用量', 'deepseek': 'DeepSeek'}
    
    def __init__(self, root: tk.Tk, theme_colors: dict,
                 on_settings: Callable, on_help: Callable, on_exit: Callable,
                 on_refresh: Callable = None, refresh_seconds: int = 60):
        self.root = root
        self.on_settings = on_settings
        self.on_help = on_help
        self.on_exit = on_exit
        self.on_refresh = on_refresh
        self.refresh_seconds = refresh_seconds
        
        self._docked_edge = 'top'  # 'top', 'bottom', 'left', 'right', or None
        self._is_visible = True
        self._animating = False
        self._hide_timer = None
        self._dragging = False
        self._user_moved = False
        self._normal_y = 8
        self._opencode_enabled = True
        self._deepseek_enabled = False
        self.window_width = self._compute_width()
        
        # Create borderless window (NO title bar at all)
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)  # Remove title bar completely
        self.window.attributes('-topmost', True)
        
        # Position
        self._screen_width = self.window.winfo_screenwidth()
        self._screen_height = self.window.winfo_screenheight()
        self._normal_x = (self._screen_width - self.window_width) // 2
        self._x = self._normal_x
        self._y = self._normal_y
        self.window.geometry(
            f"{self.window_width}x{self.EXPANDED_HEIGHT}+{self._x}+{self._y}")
        
        # Apply DWM effects after window exists
        self.window.after(10, self._setup_window_effects)
        
        # Colors
        self.text_color = '#2c3e50'
        self.accent_color = '#1976d2'
        self.subtitle_color = '#7f8c8d'
        
        # Build UI
        self._build_ui()
        self._build_context_menu()
        
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
            
            # 2. Rounded corners via window region (see _set_window_rgn).
            #    Note: DWMWCP_ROUNDSMALL is intentionally NOT used - DWM corners
            #    conflict with the region on narrow windows and cause mixed
            #    square/round corners.
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
            
            w = self.window_width
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
        # Semi-transparent content for glass effect (create once)
        if not hasattr(self, 'content') or self.content is None:
            self.content = tk.Frame(self.window, bg='#ffffff')
            self.content.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Rebuild inner content (allows switching between 3 and 4 columns)
        if getattr(self, 'inner', None):
            self.inner.destroy()
        
        inner = tk.Frame(self.content, bg='#ffffff')
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        self.inner = inner
        
        self.sections = {}
        names = []
        if self._opencode_enabled:
            names.extend(['rolling', 'weekly', 'monthly'])
        if self._deepseek_enabled:
            names.append('deepseek')
        
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
            
            # Row 2: reset time / sub status
            reset_lbl = tk.Label(sec_frame, text=self._section_reset_text(name),
                                font=('Microsoft YaHei', 8),
                                bg='#ffffff', fg=self.subtitle_color)
            reset_lbl.pack(pady=(2, 0))
            
            if i < len(names) - 1:
                sep = tk.Frame(inner, bg='#e0e0e0', width=1)
                sep.pack(side=tk.LEFT, fill=tk.Y, pady=8)
            
            self.sections[name] = {'percent': pct, 'reset': reset_lbl}
    
    def _section_reset_text(self, name: str) -> str:
        """Return the sub-line text for a section."""
        if name == 'deepseek':
            return f'余额每{self.refresh_seconds}秒刷新一次'
        return '距离重置: --'
    
    def _build_context_menu(self):
        """Build the right-click context menu (once)."""
        self.context_menu = tk.Menu(self.window, tearoff=0, bg='#ffffff', fg=self.text_color)
        self.context_menu.add_command(label='设置', command=self.on_settings)
        self.context_menu.add_command(label='帮助', command=self.on_help)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='退出', command=self.on_exit)
    
    def _compute_width(self) -> int:
        """Compute window width based on visible columns."""
        num_columns = 3 * (1 if self._opencode_enabled else 0) + (1 if self._deepseek_enabled else 0)
        return max(num_columns, 1) * self.COLUMN_WIDTH
    
    def set_columns(self, opencode_enabled: bool, deepseek_enabled: bool):
        """Set OpenCode/DeepSeek column visibility and resize the window."""
        if opencode_enabled == self._opencode_enabled and deepseek_enabled == self._deepseek_enabled:
            return
        
        self._opencode_enabled = opencode_enabled
        self._deepseek_enabled = deepseek_enabled
        self.window_width = self._compute_width()
        
        # Keep window centered at the top on first open (before user drags it)
        if not self._user_moved:
            self._normal_x = (self._screen_width - self.window_width) // 2
            self._x = self._normal_x
            self._y = self._normal_y
        
        # Rebuild column layout
        self._build_ui()
        
        # Re-apply window size and rounded region
        self.window.geometry(
            f"{self.window_width}x{self.EXPANDED_HEIGHT}+{self._x}+{self._y}")
        self.window.update_idletasks()
        try:
            hwnd = self.window.winfo_id()
            if hwnd:
                self._set_window_rgn(hwnd)
                # Force window frame refresh so the new region takes effect
                user32 = ctypes.windll.user32
                SWP_FRAMECHANGED = 0x0020
                user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                    SWP_FRAMECHANGED | 0x0002 | 0x0001 | 0x0004 | 0x0200 | 0x0040)
        except Exception:
            pass
    
    # Auto-hide
    def _schedule_check(self):
        self.window.after(100, self._check_and_schedule)
    
    def _check_and_schedule(self):
        self._check_auto_hide()
        self._schedule_check()
    
    def _detect_edge(self):
        """Detect which screen edge the window is nearest to.
        Returns 'top', 'bottom', 'left', 'right', or None."""
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        
        distances = {}
        if y < self.EDGE_THRESHOLD:
            distances['top'] = y
        if y + self.EXPANDED_HEIGHT > self._screen_height - self.EDGE_THRESHOLD:
            distances['bottom'] = self._screen_height - (y + self.EXPANDED_HEIGHT)
        if x < self.EDGE_THRESHOLD:
            distances['left'] = x
        if x + self.window_width > self._screen_width - self.EDGE_THRESHOLD:
            distances['right'] = self._screen_width - (x + self.window_width)
        
        if distances:
            # Prioritise top/bottom (horizontal toolbar) over left/right
            edge_priority = {'top': 0, 'bottom': 1, 'left': 2, 'right': 3}
            return min(distances, key=lambda e: (distances[e], edge_priority[e]))
        return None
    
    def _get_hidden_pos(self):
        """Compute the (x, y) position when the window is hidden at its docked edge."""
        if self._docked_edge == 'top':
            return (self._normal_x, -(self.EXPANDED_HEIGHT - self.COLLAPSED_SIZE))
        elif self._docked_edge == 'bottom':
            return (self._normal_x, self._screen_height - self.COLLAPSED_SIZE)
        elif self._docked_edge == 'left':
            return (-(self.window_width - self.COLLAPSED_SIZE), self._normal_y)
        elif self._docked_edge == 'right':
            return (self._screen_width - self.COLLAPSED_SIZE, self._normal_y)
        return (self._normal_x, self._normal_y)
    
    def _check_auto_hide(self):
        if self._animating or self._dragging:
            return
        
        # Refresh screen dimensions (may change when resolution changes)
        self._screen_width = self.window.winfo_screenwidth()
        self._screen_height = self.window.winfo_screenheight()
        
        # Clamp normal positions to visible screen area
        self._normal_x = max(0, min(self._normal_x, self._screen_width - self.window_width))
        self._normal_y = max(0, min(self._normal_y, self._screen_height - self.EXPANDED_HEIGHT))
        
        # Detect which edge we're near
        edge = self._detect_edge()
        if edge:
            self._docked_edge = edge
        elif not self._is_visible and self._docked_edge:
            # Hidden and no longer near an edge (e.g. screen resize) — stay docked
            pass
        else:
            # Free-floating — no auto-hide
            self._docked_edge = None
        
        if not self._docked_edge:
            # Not near any edge, ensure visible
            if not self._is_visible:
                self._animate_show()
            return
        
        mx = self.window.winfo_pointerx()
        my = self.window.winfo_pointery()
        
        # Check if mouse is in trigger zone for this edge
        in_trigger = False
        if self._docked_edge == 'top':
            in_trigger = my < self.TRIGGER_ZONE
        elif self._docked_edge == 'bottom':
            in_trigger = my > self._screen_height - self.TRIGGER_ZONE
        elif self._docked_edge == 'left':
            in_trigger = mx < self.TRIGGER_ZONE
        elif self._docked_edge == 'right':
            in_trigger = mx > self._screen_width - self.TRIGGER_ZONE
        
        # Check if mouse is inside the window
        wx = self.window.winfo_x()
        wy = self.window.winfo_y()
        wx2 = wx + self.window_width
        wy2 = wy + (self.EXPANDED_HEIGHT if self._is_visible else self.COLLAPSED_SIZE)
        inside = wx <= mx <= wx2 and wy <= my <= wy2
        
        if in_trigger or inside:
            if not self._is_visible:
                self._animate_show()
            if self._hide_timer:
                self.window.after_cancel(self._hide_timer)
                self._hide_timer = None
        else:
            if self._is_visible and not self._hide_timer:
                self._hide_timer = self.window.after(self.HIDE_DELAY, self._do_hide)
    
    def _do_hide(self):
        self._hide_timer = None
        if self._docked_edge and self._is_visible:
            self._animate_hide()
    
    # Animation
    def _animate_hide(self):
        if self._animating:
            return
        self._animating = True
        self._is_visible = False
        start = (self._normal_x, self._normal_y)
        end = self._get_hidden_pos()
        self._run_animation(start, end)
    
    def _animate_show(self):
        if self._animating:
            return
        self._animating = True
        self._is_visible = True
        start = self._get_hidden_pos()
        end = (self._normal_x, self._normal_y)
        self._run_animation(start, end)
    
    def _run_animation(self, start_pos, end_pos):
        start_time = time_module.time()
        duration = self.ANIM_DURATION / 1000.0
        
        def step():
            elapsed = time_module.time() - start_time
            t = min(elapsed / duration, 1.0)
            ease = 1 - math.pow(1 - t, 3)
            current_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * ease)
            current_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * ease)
            self._x = current_x
            self._y = current_y
            self.window.geometry(f'+{current_x}+{current_y}')
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
        self._user_moved = True
        if self._hide_timer:
            self.window.after_cancel(self._hide_timer)
            self._hide_timer = None
    
    def _on_drag(self, event):
        if not self._dragging:
            return
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self._normal_x = x
        self._normal_y = y
        self._x = x
        self._y = y
        self.window.geometry(f'+{x}+{y}')
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
                if name in self.sections:
                    self.sections[name]['percent'].configure(text='--')
                    self.sections[name]['reset'].configure(text=self._section_reset_text(name))
            return
        
        if 'deepseek_balance' in data and 'deepseek' in self.sections:
            bal = data['deepseek_balance']
            value = bal.get('balance')
            text = f"{value:.2f} 元" if value is not None else "--"
            self.sections['deepseek']['percent'].configure(text=text)
            self.sections['deepseek']['reset'].configure(
                text=f'余额每{self.refresh_seconds}秒刷新一次')
            return
        
        if 'deepseek_error' in data and 'deepseek' in self.sections:
            self.sections['deepseek']['percent'].configure(text='--')
            self.sections['deepseek']['reset'].configure(
                text=f'余额每{self.refresh_seconds}秒刷新一次')
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
