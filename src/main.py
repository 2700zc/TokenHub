"""
TokenHub - OpenCode.ai Usage Monitor
Main entry point - integrates all modules with single-instance lock.

Usage:
    python src/main.py
    Or build with PyInstaller and run dist/TokenHub/TokenHub.exe
"""

import tkinter as tk
from tkinter import messagebox
import ctypes
import threading
import queue
import time
import sys
import os

# Add parent directory to path for imports when running directly
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import Config
    from src.api import ApiClient
    from src.theme import ThemeManager
    from src.floating_window import FloatingWindow
    from src.settings_window import SettingsWindow
    from src.help_window import HelpWindow
    from src.tray import TrayIcon
    from src.logger import logger, log_startup, log_single_instance_blocked, log_refresh_triggered, log_ui_action, log_data_update, log_exception, log_deepseek, log_commandcode
else:
    from .config import Config
    from .api import ApiClient
    from .theme import ThemeManager
    from .floating_window import FloatingWindow
    from .settings_window import SettingsWindow
    from .help_window import HelpWindow
    from .tray import TrayIcon
    from .logger import logger, log_startup, log_single_instance_blocked, log_refresh_triggered, log_ui_action, log_data_update, log_exception, log_deepseek, log_commandcode


class TokenHubApp:
    """Main application class integrating all modules."""
    
    # Single instance mutex name
    MUTEX_NAME = "Global\\TokenHub_SingleInstance"
    
    REFRESH_INTERVAL = 60  # seconds
    
    def __init__(self):
        # Initialize logger first
        log_startup()
        
        # Check single instance first
        if not self._check_single_instance():
            log_single_instance_blocked()
            messagebox.showwarning("TokenHub", "TokenHub 已在运行！")
            sys.exit(1)
        
        # Initialize config
        self.config = Config()
        
        # Initialize theme
        self.theme = ThemeManager()
        logger.info(f"主题检测: {'深色' if self.theme.is_dark else '浅色'}模式")
        
        # Initialize API client with server_id from config
        self.api = ApiClient(self.config.server_id)
        
        # Create main Tk root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window
        
        # Data queue for thread-safe updates
        self.data_queue = queue.Queue()
        
        # Initialize UI components
        self.floating_window = None
        self.settings_window = None
        self.help_window = None
        self.tray = None
        
        # Initialize all UI
        self._init_ui()
        
        # Start refresh timer
        self._schedule_refresh()
    
    def _check_single_instance(self) -> bool:
        """Check if another instance is running using Windows mutex."""
        try:
            # Try to create mutex
            self._mutex = ctypes.windll.kernel32.CreateMutexW(
                None, False, self.MUTEX_NAME
            )
            # If mutex already exists, GetLastError returns ERROR_ALREADY_EXISTS (183)
            last_error = ctypes.windll.kernel32.GetLastError()
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                return False
            return True
        except Exception:
            # If mutex check fails, allow running (non-Windows or permission issue)
            return True
    
    def _init_ui(self):
        """Initialize all UI components."""
        theme_colors = self.theme.get_colors()
        theme_colors['is_dark'] = self.theme.is_dark
        
        # Create floating window
        self.floating_window = FloatingWindow(
            self.root, theme_colors,
            on_settings=self._show_settings,
            on_help=self._show_help,
            on_exit=self._exit,
            on_refresh=self._fetch_data,
            refresh_seconds=self.REFRESH_INTERVAL
        )
        self.floating_window.set_columns(self.config.opencode_enabled, self.config.deepseek_enabled, self.config.commandcode_enabled)
        
        # Create settings window (lazy - created on demand)
        self.settings_window = SettingsWindow(
            self.root, self.config, theme_colors,
            on_save=self._on_config_saved
        )
        
        # Create help window (lazy - created on demand)
        self.help_window = HelpWindow(self.root, theme_colors)
        
        # Create system tray
        self.tray = TrayIcon(
            on_show=self.floating_window.show,
            on_hide=self.floating_window.hide,
            on_settings=self._show_settings,
            on_help=self._show_help,
            on_exit=self._exit
        )
        self.tray.start()
        
        # Show initial state
        self.floating_window.update_data({'error': '等待配置'})
        
        # Check if server_id is configured (only relevant when OpenCode display is on)
        if self.config.opencode_enabled and not self.config.server_id:
            self.floating_window.update_data({'error': '请配置 Server ID'})
            logger.warning("Server ID 未配置，请在 config.json 中设置 server_id 字段")
        else:
            self._fetch_data()
    
    def _show_settings(self):
        """Show settings window."""
        log_ui_action("打开设置窗口")
        theme_colors = self.theme.get_colors()
        theme_colors['is_dark'] = self.theme.is_dark
        self.settings_window.theme_colors = theme_colors
        self.settings_window.show()
    
    def _show_help(self):
        """Show help window."""
        log_ui_action("打开帮助窗口")
        self.help_window.show()
    
    def _on_config_saved(self):
        """Called when configuration is saved."""
        logger.info("配置已保存，准备获取数据...")
        # Update API client with new server_id
        self.api.server_id = self.config.server_id
        # Apply column visibility
        self.floating_window.set_columns(self.config.opencode_enabled, self.config.deepseek_enabled, self.config.commandcode_enabled)
        # Fetch data immediately after config is saved
        if self.config.is_valid():
            logger.info("配置有效，开始获取 API 数据")
            self._fetch_data()
        else:
            logger.warning("配置无效，无法获取数据")
    
    def _fetch_data(self):
        """Fetch usage data from API."""
        def callback(result):
            # Put result in queue for main thread processing
            self.data_queue.put(result)
        
        # Fetch OpenCode.ai usage data
        if self.config.opencode_enabled and self.config.is_valid():
            logger.info("开始获取 API 数据...")
            try:
                self.api.fetch(self.config.workspace_id, self.config.cookie, callback)
            except Exception as e:
                log_exception("API 请求", e)
        elif self.config.opencode_enabled:
            logger.warning("OpenCode 配置无效，跳过用量获取")
            self.floating_window.update_data({'error': '请先配置'})
        
        # Fetch CommandCode usage (independent of OpenCode config)
        if self.config.commandcode_is_valid():
            logger.info("开始获取 CommandCode 用量...")
            try:
                self.api.fetch_commandcode(self.config.commandcode_cookie, callback)
            except Exception as e:
                log_exception("CommandCode 请求", e)
        elif self.config.commandcode_enabled:
            logger.warning("CommandCode 未配置 token，跳过用量获取")

        # Fetch DeepSeek balance + today's usage (independent of OpenCode config)
        if self.config.deepseek_is_valid():
            logger.info("开始获取 DeepSeek 余额与今日用量...")
            try:
                self.api.fetch_deepseek(self.config.deepseek_token, callback)
            except Exception as e:
                log_exception("DeepSeek 请求", e)
    
    def _process_data_queue(self):
        """Process data from queue (called from main thread)."""
        try:
            while True:
                data = self.data_queue.get_nowait()
                if 'error' in data:
                    log_data_update(error_state=True)
                    logger.error(f"数据更新失败: {data['error']}")
                elif 'cc_error' in data:
                    log_data_update(error_state=True)
                    logger.error(f"CommandCode 用量更新失败: {data['cc_error']}")
                elif 'cc' in data:
                    log_data_update(error_state=False)
                    log_commandcode(data['cc'])
                elif 'deepseek_error' in data:
                    logger.error(f"DeepSeek 数据更新失败: {data['deepseek_error']}")
                elif 'deepseek' in data:
                    log_data_update(error_state=False)
                    log_deepseek(data['deepseek'])
                else:
                    log_data_update(error_state=False)
                self.floating_window.update_data(data)
        except queue.Empty:
            pass
        
        # Schedule next queue check
        self.root.after(100, self._process_data_queue)
    
    def _schedule_refresh(self):
        """Schedule periodic data refresh."""
        log_refresh_triggered()
        # Fetch data every REFRESH_INTERVAL seconds
        self._fetch_data()
        
        # Schedule next refresh
        self.root.after(self.REFRESH_INTERVAL * 1000, self._schedule_refresh)
    
    def _exit(self):
        """Clean exit - close all windows and release mutex."""
        logger.info("TokenHub 退出")
        # Stop tray
        if self.tray:
            self.tray.stop()
        
        # Destroy floating window
        if self.floating_window:
            self.floating_window.destroy()
        
        # Release mutex
        if hasattr(self, '_mutex') and self._mutex:
            ctypes.windll.kernel32.ReleaseMutex(self._mutex)
            ctypes.windll.kernel32.CloseHandle(self._mutex)
        
        # Exit application
        self.root.quit()
    
    def run(self):
        """Run the application."""
        # Start processing data queue
        self._process_data_queue()
        
        # Run Tk main loop
        self.root.mainloop()


def main():
    """Main entry point."""
    app = TokenHubApp()
    app.run()


if __name__ == '__main__':
    main()