# TokenHub - OpenCode.ai Usage Monitor

一个 Windows 桌面悬浮小工具，实时监控 OpenCode.ai 的用量数据。

## 功能特性

- 📊 显示滚动用量、每周用量、每月用量百分比
- ⏱️ 显示各用量周期的重置倒计时
- 🎨 自动跟随 Windows 系统主题（深色/浅色）
- 🖱️ 可拖拽悬浮窗到任意位置
- 🔝 始终置顶显示
- 📍 系统托盘图标，右键菜单操作
- ⚙️ 配置持久化（Workspace ID 和 Cookie）
- 📖 内置帮助文档
- 🔒 单实例运行，防止多开

## 如何使用

### 1. 获取 Workspace ID

1. 登录 OpenCode.ai
2. 进入 Go 页面
3. 从 URL 中复制 Workspace ID（格式：`wrk_xxxxxxxxxxxx`）

### 2. 获取 Cookie

1. 在浏览器中打开 Go 页面
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 在过滤器中输入 `_server`
6. 点击 `_server` 请求
7. 在 Headers 中找到 Cookie 字符串（以 `auth=` 开头）
8. 复制完整 Cookie 字符串

### 3. 在 TokenHub 中配置

1. 右键悬浮窗，点击"设置"
2. 输入 Workspace ID 和 Cookie
3. 点击"保存"

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