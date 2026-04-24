"""
Settings window UI for TokenHub.
Allows user to input Workspace ID and Cookie.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from .config import Config

class SettingsWindow:
    """Settings window for configuring Workspace ID and Cookie."""
    
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 520
    
    def __init__(self, root: tk.Tk, config: Config, theme_colors: dict,
                 on_save: Optional[Callable] = None):
        self.root = root
        self.config = config
        self.theme_colors = theme_colors
        self.on_save = on_save
        self.window = None
    
    def show(self):
        """Show the settings window."""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.root)
        self.window.title("TokenHub 设置")
        self.window.resizable(False, False)
        
        # Center the window
        self._center_window()
        
        # Apply theme
        bg = self.theme_colors['bg']
        fg = self.theme_colors['fg']
        accent = self.theme_colors['accent']
        self.window.configure(bg=bg)
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=bg, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Workspace ID section
        ws_frame = tk.Frame(main_frame, bg=bg)
        ws_frame.pack(fill=tk.X, pady=10)
        
        ws_label = tk.Label(ws_frame, text="Workspace ID:", 
                           font=('Microsoft YaHei', 10),
                           bg=bg, fg=fg)
        ws_label.pack(anchor=tk.W)
        
        self.ws_entry = tk.Entry(ws_frame, width=50, 
                                font=('Microsoft YaHei', 10),
                                bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                                fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                                insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff')
        self.ws_entry.pack(fill=tk.X, pady=5)
        self.ws_entry.insert(0, self.config.workspace_id)
        
        # Placeholder hint
        ws_hint = tk.Label(ws_frame, text="格式: wrk_xxxxxxxxxxxx",
                          font=('Microsoft YaHei', 8),
                          bg=bg, fg=accent)
        ws_hint.pack(anchor=tk.W)
        
        # Cookie section
        cookie_frame = tk.Frame(main_frame, bg=bg)
        cookie_frame.pack(fill=tk.X, pady=10)
        
        cookie_label = tk.Label(cookie_frame, text="Cookie:",
                                font=('Microsoft YaHei', 10),
                                bg=bg, fg=fg)
        cookie_label.pack(anchor=tk.W)
        
        # Use Text widget for multi-line cookie input
        self.cookie_text = tk.Text(cookie_frame, width=50, height=4,
                                  font=('Microsoft YaHei', 10),
                                  bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                                  fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                                  insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff')
        self.cookie_text.pack(fill=tk.X, pady=5)
        self.cookie_text.insert(tk.END, self.config.cookie)
        
        cookie_hint = tk.Label(cookie_frame, text="从浏览器开发者工具复制完整 Cookie 字符串（以 auth= 开头）",
                               font=('Microsoft YaHei', 8),
                               bg=bg, fg=accent)
        cookie_hint.pack(anchor=tk.W)
        
        # Server ID section
        server_frame = tk.Frame(main_frame, bg=bg)
        server_frame.pack(fill=tk.X, pady=10)
        
        server_label = tk.Label(server_frame, text="Server ID:",
                                font=('Microsoft YaHei', 10),
                                bg=bg, fg=fg)
        server_label.pack(anchor=tk.W)
        
        self.server_entry = tk.Entry(server_frame, width=50,
                                     font=('Microsoft YaHei', 10),
                                     bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                                     fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                                     insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff')
        self.server_entry.pack(fill=tk.X, pady=5)
        self.server_entry.insert(0, self.config.server_id)
        
        server_hint = tk.Label(server_frame, text="从浏览器开发者工具的 Request Headers 中复制 X-Server-Id 的值",
                               font=('Microsoft YaHei', 8),
                               bg=bg, fg=accent)
        server_hint.pack(anchor=tk.W)
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=bg)
        btn_frame.pack(fill=tk.X, pady=15)
        
        # Button colors based on theme
        if self.theme_colors.get('is_dark', False):
            btn_bg = '#3c3c3c'
            btn_fg = '#ffffff'
            btn_active_bg = '#4fc1ff'
            btn_active_fg = '#000000'
        else:
            btn_bg = '#e5e5e5'
            btn_fg = '#000000'
            btn_active_bg = '#0078d4'
            btn_active_fg = '#ffffff'
        
        save_btn = tk.Button(btn_frame, text="保存",
                            font=('Microsoft YaHei', 11, 'bold'),
                            width=12,
                            height=1,
                            bg=btn_active_bg,
                            fg=btn_active_fg,
                            activebackground=btn_active_bg,
                            activeforeground=btn_active_fg,
                            relief=tk.RAISED,
                            bd=2,
                            command=self._save)
        save_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        cancel_btn = tk.Button(btn_frame, text="取消",
                            font=('Microsoft YaHei', 11),
                            width=12,
                            height=1,
                            bg=btn_bg,
                            fg=btn_fg,
                            activebackground='#ff6b6b',
                            activeforeground='#ffffff',
                            relief=tk.RAISED,
                            bd=2,
                            command=self._cancel)
        cancel_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Bind ESC to cancel
        self.window.bind('<Escape>', lambda e: self._cancel())
        
        # Focus on Workspace ID entry
        self.ws_entry.focus_set()
    
    def _center_window(self):
        """Center the window on screen."""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.WINDOW_WIDTH) // 2
        y = (screen_height - self.WINDOW_HEIGHT) // 2
        self.window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
    
    def _save(self):
        """Save settings and close window."""
        workspace_id = self.ws_entry.get().strip()
        cookie = self.cookie_text.get('1.0', tk.END).strip()
        server_id = self.server_entry.get().strip()
        
        # Validate inputs (basic check)
        if not workspace_id:
            messagebox.showwarning("警告", "请输入 Workspace ID")
            return
        
        if not cookie:
            messagebox.showwarning("警告", "请输入 Cookie")
            return
        
        if not server_id:
            messagebox.showwarning("警告", "请输入 Server ID")
            return
        
        # Save to config
        self.config.workspace_id = workspace_id
        self.config.cookie = cookie
        self.config.server_id = server_id
        self.config.save()
        
        # Call on_save callback if provided
        if self.on_save:
            self.on_save()
        
        self.window.destroy()
        self.window = None
    
    def _cancel(self):
        """Cancel and close window."""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def hide(self):
        """Hide the settings window."""
        if self.window:
            self.window.withdraw()