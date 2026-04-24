"""
Logger setup for TokenHub.
Provides file-based logging to track application behavior and errors.
"""

import logging
import sys
import os
from datetime import datetime

# Log file path - same directory as the executable (portable)
LOG_FILE = 'tokenhub.log'

# Configure logger
def setup_logger():
    """Setup file and console logging for TokenHub."""
    
    # Create logger
    logger = logging.getLogger('TokenHub')
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # File handler - write all logs to file
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file: timestamp - level - message
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}", file=sys.stderr)
    
    # Console handler - only warnings and errors to console (for debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    
    # Simple format for console
    console_format = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logger()

def log_startup():
    """Log application startup."""
    logger.info("=" * 60)
    logger.info("TokenHub 启动")
    logger.info("=" * 60)

def log_config_load(workspace_id: str, has_cookie: bool):
    """Log configuration load status."""
    masked_id = workspace_id[:15] + '...' if len(workspace_id) > 15 else workspace_id
    cookie_status = "已设置" if has_cookie else "未设置"
    logger.info(f"配置加载 - Workspace ID: {masked_id}, Cookie: {cookie_status}")

def log_config_save(workspace_id: str):
    """Log configuration save."""
    masked_id = workspace_id[:15] + '...' if len(workspace_id) > 15 else workspace_id
    logger.info(f"配置保存 - Workspace ID: {masked_id}")

def log_api_request(url: str):
    """Log API request URL."""
    logger.debug(f"API 请求 URL: {url[:120]}...")

def log_api_response(status_code: int, data: dict):
    """Log API response status and data."""
    logger.info(f"API 响应状态: HTTP {status_code}")
    
    # Log usage data
    for key in ['rollingUsage', 'weeklyUsage', 'monthlyUsage']:
        usage = data.get(key, {})
        percent = usage.get('usagePercent', 'N/A')
        reset_time = usage.get('reset_time', 'N/A')
        logger.info(f"  {key}: {percent}% | {reset_time}")

def log_api_error(error: str):
    """Log API error."""
    logger.error(f"API 请求失败: {error}")

def log_data_update(error_state: bool = False):
    """Log data update event."""
    if error_state:
        logger.warning("数据更新: 显示错误状态 (--%)")
    else:
        logger.info("数据更新: 悬浮窗数据已刷新")

def log_refresh_triggered():
    """Log automatic refresh triggered."""
    logger.debug("定时刷新触发")

def log_single_instance_blocked():
    """Log when another instance is detected."""
    logger.warning("检测到另一个 TokenHub 实例已在运行，当前实例退出")

def log_ui_action(action: str):
    """Log UI actions like showing settings/help."""
    logger.debug(f"UI 操作: {action}")

def log_exception(location: str, exception: Exception):
    """Log exception with traceback."""
    logger.exception(f"异常发生在 [{location}]: {exception}")