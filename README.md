# TokenHub - OpenCode.ai Usage Monitor

TokenHub 是一个轻量级的 Windows 桌面悬浮工具，零依赖、开箱即用。它能够实时监控 OpenCode Go平台的用量数据，包括滚动用量、每周用量和每月用量，并显示各周期的重置倒计时。支持自动隐藏单实例运行。

## 功能特性

- 📊 显示 OpenCode Go 的滚动用量、每周用量、每月用量百分比
- ⏱️ 显示各用量周期的重置倒计时
- 🖱️ 可拖拽悬浮窗到任意位置（贴边自动隐藏）
- 🧱 各厂商以「厂商块」纵向堆叠展示（OpenCode Go / CommandCode / DeepSeek）
- 💰 显示 DeepSeek 账户余额
- ⌘ 显示 CommandCode 用量（5小时 / 每周 / 每月 + 距离重置时间）
- ⚙️ 配置持久化（Workspace ID、Cookie、Server ID、各数据源开关与 Token）
- 📖 内置帮助文档
- 🔒 单实例运行，防止多开

## 如何使用

### 1. 获取 Workspace ID

1. 登录 OpenCode.ai
2. 进入 Go 页面
3. 从 URL 中复制 Workspace ID（格式：`wrk_xxxxxxxxxxxx`）

### 2. 获取 Cookie 和 Server ID

1. 在浏览器中打开 Go 页面
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 在过滤器中输入 `_server`
6. 点击 `_server` 请求
7. 在 Headers 中找到：
   - **Cookie**：以 `auth=` 开头的字符串
   - **X-Server-Id**：一串较长的字符
8. 分别复制这两项的值

### 3. 在 TokenHub 中配置

1. 右键悬浮窗，点击"设置"
2. 输入以下三项：
   - Workspace ID
   - Cookie
   - Server ID（从 X-Server-Id 获取）
3. 点击"保存"

### 4. （可选）显示 DeepSeek 余额

勾选"显示 DeepSeek 余额"，粘贴 platform.deepseek.com 的 Bearer Token 并保存。

### 5. （可选）显示 CommandCode 用量

勾选"显示 CommandCode 用量"，在 commandcode.ai 用量页 F12 复制任一 internal 请求的 Cookie（或 cURL），点击"从curl导入"自动提取 `__Secure-commandcode_prod_.session_token` 后保存。悬浮窗将新增一块「CommandCode」，显示 5小时 / 每周 / 每月用量百分比及距离重置时间。

每个数据源以「厂商块」纵向堆叠（宽度固定约 760px，高度随数据源数量自动增减），厂商名分别为 OpenCode Go / CommandCode / DeepSeek。

## 构建

需要 Python 3.8+ 和 PyInstaller。

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建
python build.py
# 或运行 build.bat
```

构建产物位于 `dist/TokenHub/` 目录。

## 运行

直接双击 `dist/TokenHub/TokenHub.exe` 运行，无需 Python 环境。

## 技术栈

- Python 3.8+
- tkinter（GUI）
- urllib.request（HTTP 请求）
- ctypes（系统托盘）
- PyInstaller（打包）

**零第三方依赖** - 仅使用 Python 标准库。

## 许可证

MIT License
