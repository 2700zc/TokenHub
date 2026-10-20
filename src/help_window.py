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

2. 获取 Workspace ID / Org ID：
   ◦ 登录后打开 opencode 控制台页面（如 Models 页面），其地址栏 URL 格式如下：
     https://opencode.ai/console/wrk_xxxx/models
   ◦ 请找到 URL 中 /console/ 之后的那一段字符。
     例如，在上面的链接中，wrk_xxxx 就是您的 Workspace ID。
   ◦ 操作：用鼠标选中这段 ID（如 wrk_xxxx），右键复制或按 Ctrl+C (Windows) / Command+C (Mac) 进行复制。
   ◦ 填写：将复制的 ID 粘贴到本软件的 Workspace ID 输入框中。

💡 提示：Workspace ID 通常以 wrk_ 开头，后面跟着数字和字母的组合。
（也可以直接使用下方「从curl命令导入」一键完成，推荐。）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第二步：通过浏览器开发者工具导入 curl（推荐方式）

1. 打开开发者工具：在已经打开 opencode 控制台页面的浏览器窗口中，按下键盘上的 F12 键。
   *（如果按 F12 无效，请尝试 Fn + F12，或者右键点击页面空白处，在菜单中选择"检查"/"Inspect"）*

2. 切换到 Network 标签：在开发者工具窗口的顶部菜单栏中，找到并点击 Network（网络）选项卡。

3. 刷新页面以捕获请求：
   ◦ 保持开发者工具处于打开状态，然后按 F5 或点击浏览器的刷新按钮，重新加载当前页面。

4. 筛选并找到 go/status 请求：
   ◦ 在 Network 标签页的过滤栏（Filter）中，输入 go/status。
   ◦ 找到名为 status 或路径为 /console/api/go/status 的请求项并点击它。

5. 复制 curl 命令：
   ◦ 右键该请求 → Copy → Copy as cURL（cmd/copy as cURL 均可）。
   ◦ 回到本软件的设置窗口，点击「从curl命令导入」，粘贴整段 curl 并点击「解析并填入」。
   ◦ 软件会自动提取 Workspace ID 和 Cookie（关键项是 __Host-console_session）。

手动方式（备选）：
   ◦ 在该请求的 Request Headers 中找到 Cookie: 一行，复制其中 __Host-console_session=st_xxxx... 这一段
     （连同名称和值一起复制，或整行完整 Cookie 也可以，软件会自动识别）。
   ◦ 粘贴到软件的 Cookie 输入框中。

⚠️ 注意：Cookie 是您的身份凭证，请勿泄露给他人。__Host-console_session 会定期失效，
失效后悬浮窗会提示"登录会话已失效(401)"，此时按上述步骤重新导入一次即可。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第三步：在本软件中填写

1. 将第一步中复制的 Workspace ID 粘贴到软件的对应输入框。

2. 将第二步复制的整段 curl（或其中 __Host-console_session 一段）粘贴到软件的 Cookie 输入框中。

3. 检查无误后，点击"保存"按钮即可。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第四步：显示开关（可选）

在设置窗口中可以分别控制悬浮窗显示哪些数据源，每个数据源以「厂商块」纵向堆叠显示（宽度固定，高度随开启的数据源自动增减）：

1. 显示 OpenCode 用量：开启后顶部显示一块「OpenCode Go」，内含 滚动用量 / 每周用量 / 每月用量 及其重置时间。

2. 显示 CommandCode 用量：开启后新增一块「CommandCode」，显示其 5小时（滚动）/ 每周 / 每月 用量及重置时间。

3. 显示 DeepSeek 余额：开启后新增一块「DeepSeek」，显示账户余额及刷新周期。

4. 组合效果：
   ◦ OpenCode + CommandCode + DeepSeek 全开：三块纵向排列
   ◦ 仅 OpenCode：一块
   ◦ 仅 DeepSeek：一块（只显示余额）
   ◦ 全部关闭：悬浮窗仅剩一个小空白条（可从托盘菜单操作）

悬浮窗默认停靠在屏幕顶部，靠近屏幕边缘会自动隐藏（露出 3px 边条），鼠标移入即展开；可拖拽到任意位置。

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

第六步：获取 CommandCode Session Token（可选，仅显示 CommandCode 用量时需要）

1. 登录并打开 CommandCode 用量页：在浏览器中登录 https://commandcode.ai ，打开「Usage / 用量」页面（设置中的 Usage）。

2. 获取 Session Token：
   ◦ 按 F12 打开开发者工具，切换到 Network 标签。
   ◦ 刷新页面，在请求列表中找到任意 internal 接口请求（例如 internal/usage/summary 或 internal/billing/credits）。
   ◦ 点击该请求，在 Headers 中找到 Cookie 项，里面包含 __Secure-commandcode_prod_.session_token=xxx 这一段。
   ◦ 最简单的方式：在 Network 中右键该请求 → Copy → Copy as cURL，把整段 curl 复制下来。

3. 在本软件中配置：
   ◦ 右键悬浮窗，点击「设置」。
   ◦ 勾选「显示 CommandCode 用量」，输入框变为可编辑。
   ◦ 点击「从curl导入」，把刚才复制的 curl（或整段 Cookie）粘贴进去，点击「解析并填入」，软件会自动提取 session_token。
   ◦ 也可以直接把 session_token 的值粘贴到输入框。点击「保存」。

4. 保存后悬浮窗将新增一块「CommandCode」，显示三组用量（标题沿用 滚动用量 / 每周用量 / 每月用量）：
   ◦ 滚动用量 = 5 小时滚动窗口用量百分比（如 0.19%）
   ◦ 每周用量 = 一周用量百分比（如 0.33%）
   ◦ 每月用量 = 本月额度用量百分比
   ◦ 每组下方显示距离重置的时间（5 小时/每周窗口与月额度结算日均按服务器时间倒计时）。

⚠️ 注意：Session Token 是您的账户凭证，请勿泄露给他人。软件将 Token 保存在本地 config.json 文件中。
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