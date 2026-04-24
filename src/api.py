"""
API client for fetching OpenCode.ai usage data.
Uses urllib.request (standard library) with threading for async requests.
"""

import urllib.request
import urllib.parse
import json
import threading
import re
from typing import Dict, Callable, Optional, Any

try:
    from .logger import logger, log_api_request, log_api_response, log_api_error
except ImportError:
    from logger import logger, log_api_request, log_api_response, log_api_error

class ApiClient:
    """API client for fetching OpenCode.ai usage data."""
    
    BASE_URL = "https://opencode.ai/_server"
    TIMEOUT = 10
    
    def __init__(self, server_id: str = ""):
        """Initialize API client with server ID from config."""
        self.server_id = server_id
    
    def build_url(self, workspace_id: str) -> str:
        """Build API URL with dynamic workspace_id."""
        # args parameter JSON structure (from curl command)
        args_json = {
            "t": {
                "t": 9,
                "i": 0,
                "l": 1,
                "a": [{"t": 1, "s": workspace_id}],
                "o": 0
            },
            "f": 31,
            "m": []
        }
        args_encoded = urllib.parse.quote(json.dumps(args_json))
        return f"{self.BASE_URL}?id={self.server_id}&args={args_encoded}"
    
    def build_headers(self, workspace_id: str, cookie: str) -> Dict[str, str]:
        """Build HTTP headers for the request."""
        return {
            'X-Server-Id': self.server_id,
            'X-Server-Instance': 'server-fn:0',
            'Referer': f'https://opencode.ai/workspace/{workspace_id}/go',
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch(self, workspace_id: str, cookie: str, callback: Callable[[Dict], None]):
        """Fetch usage data asynchronously in a background thread."""
        def _fetch():
            try:
                url = self.build_url(workspace_id)
                log_api_request(url)
                headers = self.build_headers(workspace_id, cookie)
                req = urllib.request.Request(url, headers=headers)
                
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    status_code = resp.getcode()
                    raw_data = resp.read().decode('utf-8')
                    logger.debug(f"API 原始响应: {raw_data[:500]}")
                    
                    # Try standard JSON first
                    try:
                        data = json.loads(raw_data)
                        result = self.parse_response(data)
                    except json.JSONDecodeError:
                        # If not JSON, try parsing as JavaScript response
                        logger.debug("标准 JSON 解析失败，尝试 JavaScript 响应解析")
                        result = self.parse_js_response(raw_data)
                    
                    log_api_response(status_code, result)
                    callback(result)
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP {e.code}: {e.reason}"
                log_api_error(error_msg)
                callback({'error': error_msg})
            except urllib.error.URLError as e:
                error_msg = f"网络错误: {e.reason}"
                log_api_error(error_msg)
                callback({'error': error_msg})
            except Exception as e:
                error_msg = str(e)
                log_api_error(error_msg)
                callback({'error': error_msg})
        
        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        return thread
    
    def parse_js_response(self, raw_text: str) -> Dict:
        """Parse JavaScript-style response (not standard JSON).
        
        Handles responses like:
        ;0x00000126;((self.$R=...$R[0]={mine:!0,...rollingUsage:$R[1]={status:"ok",resetInSec:8551,usagePercent:0}...)($R["server-fn:0"]))
        """
        result = {}
        
        # Extract usage data using regex
        # Pattern matches: rollingUsage:$R[1]={status:"ok",resetInSec:8551,usagePercent:0}
        patterns = {
            'rollingUsage': r'rollingUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:(\d+)\}',
            'weeklyUsage': r'weeklyUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:(\d+)\}',
            'monthlyUsage': r'monthlyUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:(\d+)\}'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text)
            if match:
                status = match.group(1)
                reset_sec = int(match.group(2))
                percent = int(match.group(3))
                
                result[key] = {
                    'percent': percent,
                    'reset_sec': reset_sec,
                    'reset_time': self.format_reset_time(reset_sec) if reset_sec else '--',
                    'status': status
                }
            else:
                result[key] = {
                    'percent': None,
                    'reset_sec': None,
                    'reset_time': '--',
                    'status': 'unknown'
                }
        
        return result
    
    def parse_response(self, data: Any) -> Dict:
        """Parse API response into structured usage data."""
        result = {}
        
        for key in ['rollingUsage', 'weeklyUsage', 'monthlyUsage']:
            usage = data.get(key, {})
            percent = usage.get('usagePercent', None)
            reset_sec = usage.get('resetInSec', None)
            status = usage.get('status', 'unknown')
            
            result[key] = {
                'percent': percent,
                'reset_sec': reset_sec,
                'reset_time': self.format_reset_time(reset_sec) if reset_sec else '--',
                'status': status
            }
        
        return result
    
    def format_reset_time(self, seconds: int) -> str:
        """Convert seconds to human-readable format.
        
        Rolling (< 24h): X小时Y分后重置
        Weekly/Monthly (>= 24h): X天Y小时Z分后重置
        """
        if seconds is None or seconds < 0:
            return '--'
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 0:
            return f"{days}天{hours}小时{minutes}分后重置"
        else:
            return f"{hours}小时{minutes}分后重置"