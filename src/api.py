"""
API client for fetching OpenCode.ai usage data.
Uses urllib.request (standard library) with threading for async requests.
"""

import urllib.request
import urllib.parse
import json
import threading
import re
import time
from datetime import datetime
from typing import Dict, Callable, Optional, Any

try:
    from .logger import logger, log_api_request, log_api_response, log_api_error
except ImportError:
    from logger import logger, log_api_request, log_api_response, log_api_error

COMMANDCODE_TOKEN_COOKIE = '__Secure-commandcode_prod_.session_token'


def extract_commandcode_token(raw: str) -> str:
    """Extract the CommandCode session token from various input formats.

    Accepts:
      - a full curl command copied from the browser (Windows cmd '^' escapes ok)
      - a raw Cookie string (the -b "..." value)
      - the bare session token value itself

    Returns the token verbatim (keeps any URL-encoding, matching how the
    browser stores/sends the cookie). Returns '' when nothing is found.
    """
    if not raw:
        return ''
    # Strip Windows cmd line-continuation / escape carets
    text = re.sub(r'\^[ \t]*\r?\n', '', raw)
    text = re.sub(r'\^(.)', r'\1', text)
    # 1) Named cookie inside a full cookie/curl string
    match = re.search(
        re.escape(COMMANDCODE_TOKEN_COOKIE) + r'=([^;\s"\']+)', text)
    if match:
        return match.group(1).strip()
    # 2) Looks like a full cookie but that cookie is absent -> cannot recover
    if re.search(r'[;=]', text):
        return ''
    # 3) Possibly a bare token pasted alone (long dot-separated value)
    match = re.search(r'([A-Za-z0-9_\-~.%]{40,})', text)
    if match:
        return match.group(1).strip()
    return ''


def _cc_num(value: Any) -> Optional[float]:
    """Convert a possibly-string numeric value to float (None-safe)."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cc_parse_iso_timestamp(value: Any) -> Optional[int]:
    """Parse an ISO-8601 timestamp (e.g. 2026-10-07T13:43:17.000Z) to epoch sec."""
    if not value:
        return None
    try:
        normalized = str(value).strip().replace('Z', '+00:00')
        return int(datetime.fromisoformat(normalized).timestamp())
    except (ValueError, TypeError):
        return None

class ApiClient:
    """API client for fetching OpenCode.ai usage data."""
    
    BASE_URL = "https://opencode.ai/_server"
    TIMEOUT = 10
    
    DEEPSEEK_BALANCE_URL = "https://platform.deepseek.com/api/v0/users/get_user_summary"
    DEEPSEEK_USAGE_URL = "https://platform.deepseek.com/api/v0/usage/by_api_key/amount"
    DEEPSEEK_TIMEOUT = 10
    
    COMMANDCODE_CREDITS_URL = "https://api.commandcode.ai/internal/billing/credits"
    COMMANDCODE_SUBSCRIPTIONS_URL = "https://api.commandcode.ai/internal/billing/subscriptions"
    COMMANDCODE_TIMEOUT = 10
    
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
        # Matches both old format: ...usagePercent:0}
        # and new format: ...usagePercent:19.3,usage:231665560,limit:1200000000}
        patterns = {
            'rollingUsage': r'rollingUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:([\d.]+)',
            'weeklyUsage': r'weeklyUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:([\d.]+)',
            'monthlyUsage': r'monthlyUsage:\$R\[\d+\]=\{status:"([^"]+)",resetInSec:(\d+),usagePercent:([\d.]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text)
            if match:
                status = match.group(1)
                reset_sec = int(match.group(2))
                percent = float(match.group(3))
                
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
    
    def fetch_deepseek_balance(self, token: str, callback: Callable[[Dict], None]):
        """Fetch DeepSeek account balance asynchronously in a background thread."""
        def _fetch():
            try:
                headers = {
                    'Accept': '*/*',
                    'Authorization': f'Bearer {token}',
                    'X-Client-Bundle-Id': 'com.deepseek.chat',
                    'X-Client-Locale': 'zh_CN',
                    'X-Client-Platform': 'web',
                    'X-Client-Timezone-Offset': '28800',
                    'X-Client-Version': '1.0.0',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                req = urllib.request.Request(self.DEEPSEEK_BALANCE_URL, headers=headers)
                log_api_request(self.DEEPSEEK_BALANCE_URL)
                
                with urllib.request.urlopen(req, timeout=self.DEEPSEEK_TIMEOUT) as resp:
                    status_code = resp.getcode()
                    raw_data = resp.read().decode('utf-8')
                    data = json.loads(raw_data)
                    result = self.parse_deepseek_balance(data)
                    
                    log_api_response(status_code, result)
                    callback(result)
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP {e.code}: {e.reason}"
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})
            except urllib.error.URLError as e:
                error_msg = f"网络错误: {e.reason}"
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})
            except Exception as e:
                error_msg = str(e)
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})
        
        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        return thread
    
    def parse_deepseek_balance(self, data: Any) -> Dict:
        """Parse DeepSeek get_user_summary response into balance data.
        
        Expected structure:
        {"code":0,"msg":"","data":{"biz_data":{"normal_wallets":[
            {"currency":"USD","balance":"0E-16","token_estimation":"0"},
            {"currency":"CNY","balance":"51.76","token_estimation":"0"}],
            "total_costs":[{"currency":"CNY","amount":"53.24"}]}}}
        """
        if data.get('code') != 0:
            return {'deepseek_error': f"接口返回错误: {data.get('msg', '未知错误')}"}
        
        biz_data = (data.get('data') or {}).get('biz_data') or {}
        wallets = biz_data.get('normal_wallets') or []
        
        balance = None
        currency = None
        for wallet in wallets:
            if wallet.get('currency') == 'CNY':
                balance = wallet.get('balance')
                currency = 'CNY'
                break
        if balance is None and wallets:
            balance = wallets[0].get('balance')
            currency = wallets[0].get('currency')
        
        if balance is None:
            return {'deepseek_error': '响应中未找到余额数据'}
        
        try:
            balance_num = float(balance)
        except (TypeError, ValueError):
            return {'deepseek_error': f"余额格式异常: {balance}"}
        
        return {'deepseek_balance': {'balance': balance_num, 'currency': currency or 'CNY'}}

    # ------------------------------------------------------------------
    # DeepSeek (balance + today's usage)
    # ------------------------------------------------------------------

    def build_deepseek_headers(self, token: str) -> Dict[str, str]:
        """Build HTTP headers for DeepSeek platform endpoints."""
        tz_offset = int(self._local_tz_offset_sec())
        return {
            'Accept': '*/*',
            'Authorization': f'Bearer {token}',
            'X-Client-Bundle-Id': 'com.deepseek.chat',
            'X-Client-Locale': 'zh_CN',
            'X-Client-Platform': 'web',
            'X-Client-Timezone-Offset': str(tz_offset),
            'X-Client-Version': '1.0.0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    @staticmethod
    def _local_tz_offset_sec() -> float:
        """Return the local timezone offset in seconds (east of UTC)."""
        offset = datetime.now().astimezone().utcoffset()
        return offset.total_seconds() if offset else 0.0

    @staticmethod
    def _deepseek_today_range():
        """Return the (start_sec, end_sec) of the full current local day.

        The DeepSeek usage API only accepts windows aligned to whole day
        boundaries, so we request [today 00:00, tomorrow 00:00) in local time.
        """
        now_dt = datetime.now()
        start_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt.replace(day=start_dt.day + 1)
        return int(start_dt.timestamp()), int(end_dt.timestamp())

    def _ds_balance_from_summary(self, data: Any):
        """Extract (balance, currency) from a get_user_summary payload. Raises on failure."""
        if data.get('code') != 0:
            raise ValueError(f"接口返回错误: {data.get('msg', '未知错误')}")
        biz_data = (data.get('data') or {}).get('biz_data') or {}
        wallets = biz_data.get('normal_wallets') or []
        balance = None
        currency = None
        for wallet in wallets:
            if wallet.get('currency') == 'CNY':
                balance = wallet.get('balance')
                currency = 'CNY'
                break
        if balance is None and wallets:
            balance = wallets[0].get('balance')
            currency = wallets[0].get('currency')
        if balance is None:
            raise ValueError('响应中未找到余额数据')
        return float(balance), currency or 'CNY'

    def _ds_get(self, url: str, token: str) -> Any:
        """Synchronous GET to a DeepSeek endpoint with Bearer auth."""
        req = urllib.request.Request(url, headers=self.build_deepseek_headers(token))
        log_api_request(url)
        with urllib.request.urlopen(req, timeout=self.DEEPSEEK_TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def parse_deepseek_usage(self, data: Any) -> Dict:
        """Parse /api/v0/usage/by_api_key/amount into today's request & token totals.

        Expected biz_data:
          series: [ { api_key, model, buckets: [ { time, usage: {
             REQUEST, RESPONSE_TOKEN, PROMPT_CACHE_HIT_TOKEN, PROMPT_CACHE_MISS_TOKEN } } ] } ]
        """
        if data.get('code') not in (0, None):
            raise ValueError(f"接口返回错误: {data.get('msg', '未知错误')}")
        biz_data = (data.get('data') or {}).get('biz_data') or {}
        series = biz_data.get('series') or []
        requests = 0
        tokens = 0
        for series_item in series:
            for bucket in (series_item.get('buckets') or []):
                usage = bucket.get('usage') or {}
                requests += int(usage.get('REQUEST') or 0)
                tokens += (int(usage.get('RESPONSE_TOKEN') or 0)
                           + int(usage.get('PROMPT_CACHE_HIT_TOKEN') or 0)
                           + int(usage.get('PROMPT_CACHE_MISS_TOKEN') or 0))
        return {'requests': requests, 'tokens': tokens}

    def fetch_deepseek(self, token: str, callback: Callable[[Dict], None]):
        """Fetch DeepSeek balance + today's usage asynchronously."""
        def _fetch():
            try:
                start, end = self._deepseek_today_range()
                tz = int(self._local_tz_offset_sec())
                summary = self._ds_get(self.DEEPSEEK_BALANCE_URL, token)
                balance, currency = self._ds_balance_from_summary(summary)
                usage_url = f"{self.DEEPSEEK_USAGE_URL}?start={start}&end={end}&tz={tz}"
                usage_data = self._ds_get(usage_url, token)
                usage = self.parse_deepseek_usage(usage_data)
                result = {'deepseek': {
                    'balance': balance,
                    'currency': currency,
                    'requests': usage['requests'],
                    'tokens': usage['tokens'],
                }}
                log_api_response(200, result)
                callback(result)
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP {e.code}: {e.reason}"
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})
            except urllib.error.URLError as e:
                error_msg = f"网络错误: {e.reason}"
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})
            except Exception as e:
                error_msg = str(e)
                log_api_error(error_msg)
                callback({'deepseek_error': error_msg})

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        return thread

    # ------------------------------------------------------------------
    # CommandCode
    # ------------------------------------------------------------------

    def build_cc_headers(self, token: str) -> Dict[str, str]:
        """Build HTTP headers for CommandCode internal API requests."""
        return {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Origin': 'https://commandcode.ai',
            'Referer': 'https://commandcode.ai/',
            'Cookie': f'{COMMANDCODE_TOKEN_COOKIE}={token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def _cc_get(self, url: str, token: str) -> Any:
        """Perform a synchronous GET to a CommandCode endpoint and return parsed JSON."""
        req = urllib.request.Request(url, headers=self.build_cc_headers(token))
        log_api_request(url)
        with urllib.request.urlopen(req, timeout=self.COMMANDCODE_TIMEOUT) as resp:
            raw_data = resp.read().decode('utf-8')
            return json.loads(raw_data)

    def fetch_commandcode(self, token: str, callback: Callable[[Dict], None]):
        """Fetch CommandCode usage (5-hour / weekly / monthly) asynchronously."""
        def _fetch():
            try:
                credits_data = self._cc_get(self.COMMANDCODE_CREDITS_URL, token)
                period_end = None
                try:
                    subs_data = self._cc_get(self.COMMANDCODE_SUBSCRIPTIONS_URL, token)
                    period_end = ((subs_data or {}).get('data') or {}).get('currentPeriodEnd')
                except Exception:
                    period_end = None
                result = {'cc': self.parse_commandcode(credits_data, period_end)}
                log_api_response(200, result)
                callback(result)
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP {e.code}: {e.reason}"
                log_api_error(error_msg)
                callback({'cc_error': error_msg})
            except urllib.error.URLError as e:
                error_msg = f"网络错误: {e.reason}"
                log_api_error(error_msg)
                callback({'cc_error': error_msg})
            except Exception as e:
                error_msg = str(e)
                log_api_error(error_msg)
                callback({'cc_error': error_msg})

        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
        return thread

    def _cc_make_segment(self, used: Optional[float], cap: Optional[float],
                         reset_at_ms: Any, unlimited: bool = False) -> Dict:
        """Build one usage segment ({rolling, weekly, monthly}) dict."""
        if unlimited:
            return {'percent': None, 'reset_sec': None, 'reset_time': '--',
                    'status': 'unlimited'}
        if used is None or cap is None or cap <= 0:
            return {'percent': None, 'reset_sec': None, 'reset_time': '--',
                    'status': 'unavailable'}
        percent = used / cap * 100.0
        reset_sec = None
        if reset_at_ms:
            reset_sec = max(0, int(reset_at_ms / 1000.0 - time.time()))
        return {
            'percent': percent,
            'reset_sec': reset_sec,
            'reset_time': self.format_reset_time(reset_sec) if reset_sec is not None else '--',
            'status': 'ok'
        }

    def parse_commandcode(self, data: Any, period_end: Any = None) -> Dict:
        """Parse the /internal/billing/credits response into rolling/weekly/monthly.

        Expected shape (verified live):
          credits: { monthlyCredits, monthlyCreditsGranted, ... }
          windowLimits: {
             limited: bool,
             fiveHour: { used, cap, exceeded, resetAt (epoch ms) },
             weekly:   { used, cap, exceeded, resetAt (epoch ms) }
          }
        Monthly usage = (granted - remaining) / granted.
        Monthly reset time is taken from the subscription currentPeriodEnd.
        """
        window_limits = (data or {}).get('windowLimits') or {}
        credits = (data or {}).get('credits') or {}
        limited = window_limits.get('limited', True)

        five = window_limits.get('fiveHour') or {}
        weekly = window_limits.get('weekly') or {}

        unlimited = limited is False
        rolling = self._cc_make_segment(
            _cc_num(five.get('used')), _cc_num(five.get('cap')),
            five.get('resetAt'), unlimited=unlimited)
        week = self._cc_make_segment(
            _cc_num(weekly.get('used')), _cc_num(weekly.get('cap')),
            weekly.get('resetAt'), unlimited=unlimited)

        granted = _cc_num(credits.get('monthlyCreditsGranted'))
        remaining = _cc_num(credits.get('monthlyCredits'))
        monthly_used = (granted - remaining) if (granted is not None and remaining is not None) else None
        monthly = self._cc_make_segment(monthly_used, granted, None)
        if monthly['status'] == 'ok' and period_end:
            end_sec = _cc_parse_iso_timestamp(period_end)
            if end_sec is not None:
                reset_sec = max(0, int(end_sec - time.time()))
                monthly['reset_sec'] = reset_sec
                monthly['reset_time'] = self.format_reset_time(reset_sec)

        return {'rolling': rolling, 'weekly': week, 'monthly': monthly}