"""
Settings window UI for TokenHub.
Allows user to input Workspace ID and Cookie.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
import re
import urllib.parse
from .config import Config


def parse_curl_text(text: str) -> dict:
    """Parse curl command text to extract workspace_id, cookie, server_id."""
    text = re.sub(r'\^[ \t]*\r?\n', '', text)
    text = re.sub(r'\^(.)', r'\1', text)

    result = {}

    match = re.search(r'-H\s+"[Xx]-[Ss]erver-[Ii][Dd]:\s*([^"]+)"', text)
    if match:
        result['server_id'] = match.group(1).strip()

    if 'server_id' not in result:
        match = re.search(r'\?id=([a-f0-9]+)', text)
        if match:
            result['server_id'] = match.group(1).strip()

    match = re.search(r'-H\s+"[Cc]ookie:\s*([^"]+)"', text)
    if match:
        result['cookie'] = match.group(1).strip()
    else:
        match = re.search(r'-b\s+"([^"]+)"', text)
        if match:
            result['cookie'] = match.group(1).strip()

    match = re.search(r'/workspace/(wrk_[^"\s/]+)', text, re.IGNORECASE)
    if match:
        result['workspace_id'] = match.group(1).strip()

    if 'workspace_id' not in result:
        match = re.search(r'%22s%22%3A%22(wrk_[^%]+)%22', text)
        if match:
            result['workspace_id'] = urllib.parse.unquote(match.group(1))

    return result


class SettingsWindow:
    """Settings window for configuring Workspace ID and Cookie."""
    
    WINDOW_WIDTH = 520
    WINDOW_HEIGHT = 580
    
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
        
        # Action buttons row: Import curl and Reset side by side
        action_frame = tk.Frame(server_frame, bg=bg)
        action_frame.pack(fill=tk.X, pady=(8, 0))

        import_btn = tk.Button(action_frame, text="从curl命令导入",
                               font=('Microsoft YaHei', 9),
                               bg=btn_bg, fg=btn_fg,
                               activebackground=btn_active_bg,
                               activeforeground=btn_active_fg,
                               relief=tk.RAISED, bd=1,
                               command=self._show_curl_import_dialog)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = tk.Button(action_frame, text="重置",
                              font=('Microsoft YaHei', 9),
                              bg=btn_bg, fg=btn_fg,
                              activebackground='#ff6b6b',
                              activeforeground='#ffffff',
                              relief=tk.RAISED, bd=1,
                              command=self._reset)
        reset_btn.pack(side=tk.LEFT)
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=bg)
        btn_frame.pack(fill=tk.X, pady=15)
        
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
    
    def _reset(self):
        """Clear all input fields."""
        self.ws_entry.delete(0, tk.END)
        self.cookie_text.delete('1.0', tk.END)
        self.server_entry.delete(0, tk.END)

    def _show_curl_import_dialog(self):
        """Show a dialog for pasting curl command and auto-filling fields."""
        dialog = tk.Toplevel(self.window)
        dialog.title("从curl命令导入")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        bg = self.theme_colors['bg']
        fg = self.theme_colors['fg']
        accent = self.theme_colors['accent']
        dialog.configure(bg=bg)

        dw = 560
        dh = 360
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        frame = tk.Frame(dialog, bg=bg, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="将完整的 curl 命令粘贴到下方文本框中：",
                 font=('Microsoft YaHei', 10),
                 bg=bg, fg=fg).pack(anchor=tk.W)

        text_widget = tk.Text(frame, width=60, height=10,
                              font=('Consolas', 10),
                              bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                              fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                              insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                              wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=8)
        text_widget.focus_set()

        btn_frame = tk.Frame(frame, bg=bg)
        btn_frame.pack(fill=tk.X)

        def on_parse():
            curl_text = text_widget.get('1.0', tk.END).strip()
            if not curl_text:
                messagebox.showwarning("警告", "请先粘贴 curl 命令", parent=dialog)
                return

            parsed = parse_curl_text(curl_text)
            missing = []
            if not parsed.get('workspace_id'):
                missing.append("Workspace ID")
            if not parsed.get('cookie'):
                missing.append("Cookie")
            if not parsed.get('server_id'):
                missing.append("Server ID")

            if parsed.get('workspace_id'):
                self.ws_entry.delete(0, tk.END)
                self.ws_entry.insert(0, parsed['workspace_id'])
            if parsed.get('cookie'):
                self.cookie_text.delete('1.0', tk.END)
                self.cookie_text.insert(tk.END, parsed['cookie'])
            if parsed.get('server_id'):
                self.server_entry.delete(0, tk.END)
                self.server_entry.insert(0, parsed['server_id'])

            if missing:
                msg = f"成功导入以下字段：\n" \
                      f"  Workspace ID: {'✓' if parsed.get('workspace_id') else '✗'}\n" \
                      f"  Cookie: {'✓' if parsed.get('cookie') else '✗'}\n" \
                      f"  Server ID: {'✓' if parsed.get('server_id') else '✗'}\n\n" \
                      f"以下字段未能自动识别，请手动填写：\n- " + "\n- ".join(missing)
                messagebox.showinfo("部分导入成功", msg, parent=dialog)
            else:
                messagebox.showinfo("导入成功", "所有字段已自动填入，请点击「保存」确认。", parent=dialog)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        if self.theme_colors.get('is_dark', False):
            btn_bg_d = '#3c3c3c'
            btn_fg_d = '#ffffff'
            btn_active_d = '#4fc1ff'
            btn_active_fg_d = '#000000'
        else:
            btn_bg_d = '#e5e5e5'
            btn_fg_d = '#000000'
            btn_active_d = '#0078d4'
            btn_active_fg_d = '#ffffff'

        parse_btn = tk.Button(btn_frame, text="解析并填入",
                              font=('Microsoft YaHei', 10, 'bold'),
                              bg=btn_active_d, fg=btn_active_fg_d,
                              activebackground=btn_active_d,
                              activeforeground=btn_active_fg_d,
                              relief=tk.RAISED, bd=2,
                              command=on_parse)
        parse_btn.pack(side=tk.LEFT, padx=6)

        cancel_btn = tk.Button(btn_frame, text="取消",
                               font=('Microsoft YaHei', 10),
                               bg=btn_bg_d, fg=btn_fg_d,
                               activebackground='#ff6b6b',
                               activeforeground='#ffffff',
                               relief=tk.RAISED, bd=2,
                               command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=6)

        dialog.bind('<Escape>', lambda e: on_cancel())

    def hide(self):
        """Hide the settings window."""
        if self.window:
            self.window.withdraw()