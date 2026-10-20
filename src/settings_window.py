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
from .app_icon import get_app_icon, set_window_icon

try:
    from .api import extract_commandcode_token
except ImportError:
    from api import extract_commandcode_token


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

    # New console API: x-org-id header and /console/<wrk_...>/... paths
    if 'workspace_id' not in result:
        match = re.search(r'[Xx]-[Oo]rg-[Ii][Dd]:\s*([a-zA-Z0-9_]+)', text)
        if match:
            result['workspace_id'] = match.group(1).strip()

    if 'workspace_id' not in result:
        match = re.search(r'/console/(wrk_[^"\s/]+)', text, re.IGNORECASE)
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
    WINDOW_HEIGHT = 760
    
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
        set_window_icon(self.window.winfo_id(), get_app_icon(32))
        
        # Center the window
        self._center_window()
        
        # Apply theme
        bg = self.theme_colors['bg']
        fg = self.theme_colors['fg']
        accent = self.theme_colors['accent']
        self.window.configure(bg=bg)
        
        # Outer container (form scrolls, buttons stay pinned at the bottom)
        container = tk.Frame(self.window, bg=bg)
        container.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(container, bg=bg)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 14))
        
        self._canvas = tk.Canvas(container, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL,
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        main_frame = tk.Frame(self._canvas, bg=bg, padx=20, pady=16)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=main_frame, anchor='nw')
        main_frame.bind('<Configure>', self._on_form_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)
        self.window.bind('<MouseWheel>', self._on_mousewheel)
        
        entry_bg = '#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d'
        entry_fg = '#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff'
        
        # OpenCode display switch (top)
        opencode_frame = tk.Frame(main_frame, bg=bg)
        opencode_frame.pack(fill=tk.X, pady=10)
        
        self.opencode_var = tk.BooleanVar(value=self.config.opencode_enabled)
        opencode_check = tk.Checkbutton(opencode_frame, text="显示 OpenCode 用量",
                                        variable=self.opencode_var,
                                        font=('Microsoft YaHei', 10, 'bold'),
                                        bg=bg, fg=fg,
                                        activebackground=bg, activeforeground=fg,
                                        selectcolor=bg,
                                        command=self._on_opencode_toggle)
        opencode_check.pack(anchor=tk.W)
        
        opencode_hint = tk.Label(opencode_frame, text="开启后显示滚动/每周/每月用量三列",
                                 font=('Microsoft YaHei', 8),
                                 bg=bg, fg=accent)
        opencode_hint.pack(anchor=tk.W)
        
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
        
        cookie_hint = tk.Label(cookie_frame, text="从浏览器开发者工具复制完整 Cookie 或整段 curl（需要包含 __Host-console_session）",
                               font=('Microsoft YaHei', 8),
                               bg=bg, fg=accent)
        cookie_hint.pack(anchor=tk.W)
        
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
        action_frame = tk.Frame(main_frame, bg=bg)
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
        
        # CommandCode section
        cc_frame = tk.Frame(main_frame, bg=bg)
        cc_frame.pack(fill=tk.X, pady=10)
        
        self.commandcode_var = tk.BooleanVar(value=self.config.commandcode_enabled)
        cc_check = tk.Checkbutton(cc_frame, text="显示 CommandCode 用量",
                                   variable=self.commandcode_var,
                                   font=('Microsoft YaHei', 10, 'bold'),
                                   bg=bg, fg=fg,
                                   activebackground=bg, activeforeground=fg,
                                   selectcolor=bg,
                                   command=self._on_commandcode_toggle)
        cc_check.pack(anchor=tk.W)
        
        cc_hint = tk.Label(cc_frame, text="开启后显示 CommandCode 的 5小时/每周/每月用量（CC 前缀三列）",
                           font=('Microsoft YaHei', 8),
                           bg=bg, fg=accent)
        cc_hint.pack(anchor=tk.W)
        
        cc_token_frame = tk.Frame(cc_frame, bg=bg)
        cc_token_frame.pack(fill=tk.X, pady=(6, 0))
        
        cc_token_label = tk.Label(cc_token_frame, text="CommandCode Session Token:",
                                  font=('Microsoft YaHei', 10),
                                  bg=bg, fg=fg)
        cc_token_label.pack(anchor=tk.W)
        
        self.commandcode_entry = tk.Entry(cc_token_frame, width=50,
                                          font=('Microsoft YaHei', 10),
                                          bg=entry_bg, fg=entry_fg,
                                          insertbackground=entry_fg)
        self.commandcode_entry.pack(fill=tk.X, pady=5)
        self.commandcode_entry.insert(0, self.config.commandcode_cookie)
        
        cc_btn_row = tk.Frame(cc_token_frame, bg=bg)
        cc_btn_row.pack(fill=tk.X, pady=(2, 0))
        
        cc_import_btn = tk.Button(cc_btn_row, text="从curl导入",
                                  font=('Microsoft YaHei', 9),
                                  bg=btn_bg, fg=btn_fg,
                                  activebackground=btn_active_bg,
                                  activeforeground=btn_active_fg,
                                  relief=tk.RAISED, bd=1,
                                  command=self._show_commandcode_curl_dialog)
        cc_import_btn.pack(side=tk.LEFT)
        
        cc_token_hint = tk.Label(cc_token_frame,
                                 text="打开 commandcode.ai 用量页，F12→Network 复制任一 internal 请求的 Cookie，软件自动提取 session_token",
                                 font=('Microsoft YaHei', 8),
                                 bg=bg, fg=accent,
                                 justify=tk.LEFT, wraplength=460)
        cc_token_hint.pack(anchor=tk.W, pady=(4, 0))
        
        if not self.commandcode_var.get():
            self.commandcode_entry.config(state='disabled')
        
        # DeepSeek section
        deepseek_frame = tk.Frame(main_frame, bg=bg)
        deepseek_frame.pack(fill=tk.X, pady=10)
        
        self.deepseek_var = tk.BooleanVar(value=self.config.deepseek_enabled)
        deepseek_check = tk.Checkbutton(deepseek_frame, text="显示 DeepSeek 余额",
                                        variable=self.deepseek_var,
                                        font=('Microsoft YaHei', 10),
                                        bg=bg, fg=fg,
                                        activebackground=bg, activeforeground=fg,
                                        selectcolor=bg,
                                        command=self._on_deepseek_toggle)
        deepseek_check.pack(anchor=tk.W)
        
        ds_token_frame = tk.Frame(deepseek_frame, bg=bg)
        ds_token_frame.pack(fill=tk.X, pady=(6, 0))
        
        ds_token_label = tk.Label(ds_token_frame, text="DeepSeek Token (Bearer):",
                                  font=('Microsoft YaHei', 10),
                                  bg=bg, fg=fg)
        ds_token_label.pack(anchor=tk.W)
        
        self.deepseek_token_entry = tk.Entry(ds_token_frame, width=50,
                                             font=('Microsoft YaHei', 10),
                                             bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                                             fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                                             insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff')
        self.deepseek_token_entry.pack(fill=tk.X, pady=5)
        self.deepseek_token_entry.insert(0, self.config.deepseek_token)
        
        ds_token_hint = tk.Label(ds_token_frame, text="从 DeepSeek 开放平台（platform.deepseek.com）复制 Token，可含 Bearer 前缀",
                                 font=('Microsoft YaHei', 8),
                                 bg=bg, fg=accent)
        ds_token_hint.pack(anchor=tk.W)
        
        if not self.deepseek_var.get():
            self.deepseek_token_entry.config(state='disabled')
        
        # Apply OpenCode input enable/disable state
        self._apply_opencode_state()
        
        # Buttons (pinned at the bottom of the window)
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
        save_btn.pack(side=tk.LEFT, padx=6, pady=4)
        
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
        cancel_btn.pack(side=tk.LEFT, padx=6, pady=4)
        
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
    
    def _on_form_configure(self, event):
        """Update the canvas scroll region when the form size changes."""
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Make the form width follow the canvas width."""
        if hasattr(self, '_canvas_window'):
            self._canvas.itemconfigure(self._canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        """Scroll the settings form with the mouse wheel."""
        if hasattr(self, '_canvas'):
            self._canvas.yview_scroll(int(-event.delta / 120), 'units')
    
    def _on_commandcode_toggle(self):
        """Enable/disable the CommandCode token input based on checkbox state."""
        if self.commandcode_var.get():
            self.commandcode_entry.config(state='normal')
            self.commandcode_entry.focus_set()
        else:
            self.commandcode_entry.config(state='disabled')
    
    def _on_deepseek_toggle(self):
        """Enable/disable the DeepSeek token input based on checkbox state."""
        if self.deepseek_var.get():
            self.deepseek_token_entry.config(state='normal')
            self.deepseek_token_entry.focus_set()
        else:
            self.deepseek_token_entry.config(state='disabled')
    
    def _on_opencode_toggle(self):
        """Enable/disable the OpenCode input fields based on checkbox state."""
        self._apply_opencode_state()
        if self.opencode_var.get():
            self.ws_entry.focus_set()
    
    def _apply_opencode_state(self):
        """Apply enabled/disabled state to the OpenCode input fields."""
        state = 'normal' if self.opencode_var.get() else 'disabled'
        self.ws_entry.config(state=state)
        self.cookie_text.config(state=state)
    
    def _save(self):
        """Save settings and close window."""
        workspace_id = self.ws_entry.get().strip()
        cookie = self.cookie_text.get('1.0', tk.END).strip()
        opencode_enabled = self.opencode_var.get()
        deepseek_enabled = self.deepseek_var.get()
        deepseek_token = self.deepseek_token_entry.get().strip()
        
        # Validate OpenCode inputs only when OpenCode display is enabled
        if opencode_enabled:
            if not workspace_id:
                messagebox.showwarning("警告", "请输入 Workspace ID")
                return
            
            if not cookie:
                messagebox.showwarning("警告", "请输入 Cookie")
                return
        
        # Validate DeepSeek token only when DeepSeek display is enabled
        if deepseek_enabled and not deepseek_token:
            messagebox.showwarning("警告", "启用 DeepSeek 余额显示需要填写 Token")
            return
        
        # Strip "Bearer " prefix if user pasted the full header value
        if deepseek_token.lower().startswith('bearer '):
            deepseek_token = deepseek_token[7:].strip()
        
        # CommandCode token: normalize whatever was pasted (cookie/curl/raw)
        commandcode_enabled = self.commandcode_var.get()
        commandcode_raw = self.commandcode_entry.get().strip()
        commandcode_token = extract_commandcode_token(commandcode_raw) if commandcode_raw else ''
        if commandcode_enabled and not commandcode_token:
            messagebox.showwarning(
                "警告",
                "启用 CommandCode 用量显示需要填写有效的 Session Token\n（可直接粘贴整段 Cookie 或 curl 命令）")
            return
        
        # Save to config
        self.config.workspace_id = workspace_id
        self.config.cookie = cookie
        self.config.opencode_enabled = opencode_enabled
        self.config.deepseek_enabled = deepseek_enabled
        self.config.deepseek_token = deepseek_token if deepseek_enabled else ""
        self.config.commandcode_enabled = commandcode_enabled
        self.config.commandcode_cookie = commandcode_token if commandcode_enabled else ""
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
        self.opencode_var.set(True)
        self._apply_opencode_state()
        self.ws_entry.delete(0, tk.END)
        self.cookie_text.delete('1.0', tk.END)
        self.commandcode_var.set(False)
        self.commandcode_entry.delete(0, tk.END)
        self.commandcode_entry.config(state='disabled')
        self.deepseek_var.set(False)
        self.deepseek_token_entry.delete(0, tk.END)
        self.deepseek_token_entry.config(state='disabled')

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

            if parsed.get('workspace_id'):
                self.ws_entry.delete(0, tk.END)
                self.ws_entry.insert(0, parsed['workspace_id'])
            if parsed.get('cookie'):
                self.cookie_text.delete('1.0', tk.END)
                self.cookie_text.insert(tk.END, parsed['cookie'])

            if missing:
                msg = f"成功导入以下字段：\n" \
                      f"  Workspace ID: {'✓' if parsed.get('workspace_id') else '✗'}\n" \
                      f"  Cookie: {'✓' if parsed.get('cookie') else '✗'}\n\n" \
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

    def _show_commandcode_curl_dialog(self):
        """Show a dialog for pasting a CommandCode curl/Cookie and auto-filling the token."""
        dialog = tk.Toplevel(self.window)
        dialog.title("从curl导入 CommandCode")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        bg = self.theme_colors['bg']
        fg = self.theme_colors['fg']
        accent = self.theme_colors['accent']
        dialog.configure(bg=bg)

        dw = 620
        dh = 380
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        frame = tk.Frame(dialog, bg=bg, padx=16, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="粘贴 commandcode 的整段 curl 命令，或整段 Cookie（-b 的内容）：",
                 font=('Microsoft YaHei', 10), bg=bg, fg=fg,
                 justify=tk.LEFT, wraplength=580).pack(anchor=tk.W)

        text_widget = tk.Text(frame, width=60, height=10,
                              font=('Consolas', 9),
                              bg='#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d',
                              fg='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                              insertbackground='#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff',
                              wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=8)
        text_widget.focus_set()

        def on_parse():
            raw = text_widget.get('1.0', tk.END).strip()
            if not raw:
                messagebox.showwarning("警告", "请先粘贴 curl 或 Cookie", parent=dialog)
                return
            token = extract_commandcode_token(raw)
            if not token:
                messagebox.showerror(
                    "无法识别",
                    "未能从内容中识别出 session_token。\n"
                    "请确认粘贴的是 commandcode.ai 用量页任一请求的完整 Cookie（包含 "
                    "__Secure-commandcode_prod_.session_token=...）。",
                    parent=dialog)
                return
            self.commandcode_entry.delete(0, tk.END)
            self.commandcode_entry.insert(0, token)
            messagebox.showinfo("导入成功", "已提取 Session Token，请点击「保存」确认。", parent=dialog)
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

        btn_frame = tk.Frame(frame, bg=bg)
        btn_frame.pack(fill=tk.X)

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