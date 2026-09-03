"""
Help window UI for TokenHub.
Displays step-by-step tutorial for getting Workspace ID and Cookie.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

try:
    from .app_icon import get_app_icon, set_window_icon
except ImportError:
    from app_icon import get_app_icon, set_window_icon

# Help content (from requirements document)
HELP_CONTENT = """
第一步：登录并获取 Workspace ID

1. 登录系统：使用您的账号登录 OpenCode.ai 平台。

2. 进入 Go 页面：在浏览器中打开目标 Go 语言项目的页面。

3. 复制 Workspace ID：
   ◦ 请查看浏览器地址栏中的完整 URL，其格式通常如下：
     https://opencode.ai/workspace/wrk_xxxx/go
   ◦ 请找到 URL 中 /workspace/ 之后、第二个 / 之前的那一段字符。
     例如，在上面的链接中，wrk_xxxx 就是您的 Workspace ID。
   ◦ 操作：用鼠标选中这段 ID（如 wrk_xxxx），右键复制或按 Ctrl+C (Windows) / Command+C (Mac) 进行复制。
   ◦ 填写：将复制的 ID 粘贴到本软件的 Workspace ID 输入框中。

💡 提示：Workspace ID 通常以 wrk_ 开头，后面跟着数字和字母的组合。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第二步：通过浏览器开发者工具获取 Cookie

1. 打开开发者工具：在已经打开 Go 页面的浏览器窗口中，按下键盘上的 F12 键。
   *（如果按 F12 无效，请尝试 Fn + F12，或者右键点击页面空白处，在菜单中选择"检查"/"Inspect"）*

2. 切换到 Network 标签：在开发者工具窗口的顶部菜单栏中，找到并点击 Network（网络）选项卡。如果标签页内是空的，请继续下一步。

3. 刷新页面以捕获请求：
   ◦ 保持开发者工具处于打开状态，然后按 F5 或点击浏览器的刷新按钮，重新加载当前页面。
   ◦ 刷新后，您会看到 Network 标签下出现一个不断增加的请求列表（包含图片、脚本、数据等）。

4. 篮选并找到 _server 请求：
   ◦ 在 Network 标签页的过滤栏（通常是一个输入框，带有"筛选"或"Filter"字样）中，输入 _server。
   ◦ 列表将只显示包含 _server 关键字的请求。请找到名为 _server 或类似 /_server 的请求项，并点击它。

5. 提取 Cookie 值：
   ◦ 点击 _server 请求后，会出现该请求的详细子标签页。请点击 Headers（标头）选项卡。
   ◦ 向下滚动，找到 Request Headers（请求标头）区域。
   ◦ 在该区域中，找到 Cookie: 这一行。它的值会是一长串字符，其中以 auth= 开头（例如：auth=Fexxxx...; other=...）。
   ◦ 重要：您需要复制的是从 auth= 开始，直到该行结束的完整 Cookie 字符串。
   ◦ 操作：用鼠标双击 Cookie 的值部分，全选后复制（Ctrl+C / Command+C）。

6. 提取 Server ID：
   ◦ 仍在同一个 Headers 选项卡中，继续在 Request Headers 区域查找。
   ◦ 找到 X-Server-Id: 这一行。它的值是一串较长的字符（例如：c7389bd0e731f80f...）。
   ◦ 这个 Server ID 与 Cookie 在同一请求中，提取方式完全相同。
   ◦ 操作：用鼠标双击 X-Server-Id 的值部分，全选后复制（Ctrl+C / Command+C）。
   ◦ 填写：将复制的 Server ID 粘贴到 config.json 文件中的 server_id 字段内。

⚠️ 注意：Cookie 是您的身份凭证，请勿泄露给他人。请确保复制的字符串包含完整的 auth=... 及其后的所有内容，直到分号或其他字段结束。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第三步：在本软件中填写

1. 将第一步中复制的 Workspace ID 粘贴到软件的对应输入框。

2. 将第二步中复制的完整 Cookie 字符串（以 auth= 开头）粘贴到软件的 Cookie 输入框中。

3. 将第二步中复制的 Server ID 粘贴到软件的 Server ID 输入框中。

4. 检查无误后，点击"保存"按钮即可。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第四步：显示列开关（可选）

在设置窗口中可以分别控制悬浮窗显示哪些列：

1. 显示 OpenCode 用量：勾选后显示「滚动用量 / 每周用量 / 每月用量」三列，默认开启。

2. 显示 DeepSeek 余额：勾选后显示第四列「DeepSeek 余额」。

3. 组合效果：
   ◦ OpenCode 开启 + DeepSeek 开启：共 4 列（三列用量 + DeepSeek 余额）
   ◦ 仅 OpenCode 开启：3 列（用量）
   ◦ 仅 DeepSeek 开启：1 列（余额）
   ◦ 两者都关闭：悬浮窗不显示任何数据列

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第五步：获取 DeepSeek Token（可选，仅显示余额时需要）

1. 打开 DeepSeek 开放平台：在浏览器中访问 https://platform.deepseek.com 并登录。

2. 获取 Token：进入「API Keys」或账户相关页面，复制您的开发者 Token。
   ◦ 说明：需要的是平台网站的 Bearer Token（authorization 中 Bearer 后的那串字符），不是以 sk- 开头的 API Key。

3. 在本软件中配置：
   ◦ 右键悬浮窗，点击「设置」。
   ◦ 勾选「显示 DeepSeek 余额」，输入框变为可编辑。
   ◦ 将复制的 Token 粘贴到「DeepSeek Token (Bearer)」输入框中（可连同 Bearer 前缀一起粘贴，软件会自动处理）。
   ◦ 点击「保存」。

4. 保存后悬浮窗将显示 DeepSeek 账户余额（人民币金额，如 ¥51.76）。
   ◦ 余额每 60 秒自动刷新一次，将鼠标移到悬浮窗上也可手动触发刷新。

⚠️ 注意：Token 是您的账户凭证，请勿泄露给他人。软件将 Token 保存在本地 config.json 文件中。
"""

class HelpWindow:
    """Help window displaying tutorial content."""
    
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 500
    
    def __init__(self, root: tk.Tk, theme_colors: dict):
        self.root = root
        self.theme_colors = theme_colors
        self.window = None
    
    def show(self):
        """Show the help window."""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.root)
        self.window.title("TokenHub 使用帮助")
        self.window.resizable(True, True)
        set_window_icon(self.window.winfo_id(), get_app_icon(32))
        
        # Center the window
        self._center_window()
        
        # Apply theme
        bg = self.theme_colors['bg']
        fg = self.theme_colors['fg']
        accent = self.theme_colors['accent']
        self.window.configure(bg=bg)
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(main_frame, bg=bg)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_bg = '#ffffff' if not self.theme_colors.get('is_dark', False) else '#2d2d2d'
        text_fg = '#000000' if not self.theme_colors.get('is_dark', False) else '#ffffff'
        
        self.text_widget = tk.Text(text_frame, 
                                   wrap=tk.WORD,
                                   font=('Microsoft YaHei', 10),
                                   bg=text_bg, fg=text_fg,
                                   yscrollcommand=scrollbar.set,
                                   padx=10, pady=10)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        
        # Configure text tags for formatting
        self.text_widget.tag_configure('title', 
                                       font=('Microsoft YaHei', 12, 'bold'),
                                       foreground=accent)
        self.text_widget.tag_configure('warning',
                                       font=('Microsoft YaHei', 10, 'bold'),
                                       foreground='#ff6b6b')
        self.text_widget.tag_configure('hint',
                                       font=('Microsoft YaHei', 10, 'italic'),
                                       foreground=accent)
        
        # Insert content (read-only)
        self.text_widget.insert(tk.END, HELP_CONTENT)
        self.text_widget.configure(state='disabled')  # Make read-only
        
        # Close button
        btn_frame = tk.Frame(main_frame, bg=bg)
        btn_frame.pack(fill=tk.X, pady=10)
        
        close_btn = tk.Button(btn_frame, text="关闭",
                             font=('Microsoft YaHei', 10),
                             width=10,
                             command=self._close)
        close_btn.pack(side=tk.RIGHT)
        
        # Bind ESC to close
        self.window.bind('<Escape>', lambda e: self._close())
    
    def _center_window(self):
        """Center the window on screen."""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.WINDOW_WIDTH) // 2
        y = (screen_height - self.WINDOW_HEIGHT) // 2
        self.window.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
    
    def _close(self):
        """Close the help window."""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def hide(self):
        """Hide the help window."""
        if self.window:
            self.window.withdraw()