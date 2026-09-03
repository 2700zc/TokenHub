"""
Configuration manager for TokenHub.
Handles workspace_id and cookie persistence in config.json.
"""

import json
import os
import sys

try:
    from .logger import log_config_load, log_config_save
except ImportError:
    from logger import log_config_load, log_config_save

def _get_app_dir():
    """Get the directory where the application executable or script resides.
    
    When running as a PyInstaller bundle, sys.executable points to the exe.
    When running as a script, __file__ points to the source file.
    This ensures config.json is always saved next to the app, not in CWD.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))

# Resolve config path relative to the application directory
_APP_DIR = _get_app_dir()

class Config:
    """Configuration manager for TokenHub."""
    
    CONFIG_FILE = os.path.join(_APP_DIR, 'config.json')
    
    def __init__(self):
        self.workspace_id = ""
        self.cookie = ""
        self.server_id = ""
        self.opencode_enabled = True
        self.deepseek_enabled = False
        self.deepseek_token = ""
        self.load()
        log_config_load(self.workspace_id, bool(self.cookie))
    
    def load(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.CONFIG_FILE):
            self.save()  # Create default empty config
            return
        
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workspace_id = data.get('workspace_id', '')
                self.cookie = data.get('cookie', '')
                self.server_id = data.get('server_id', '')
                self.opencode_enabled = data.get('opencode_enabled', True)
                self.deepseek_enabled = data.get('deepseek_enabled', False)
                self.deepseek_token = data.get('deepseek_token', '')
        except (json.JSONDecodeError, Exception):
            # Corrupted file - reset to default
            self.workspace_id = ""
            self.cookie = ""
            self.server_id = ""
            self.opencode_enabled = True
            self.deepseek_enabled = False
            self.deepseek_token = ""
            self.save()
    
    def save(self):
        """Save configuration to JSON file."""
        data = {
            'workspace_id': self.workspace_id,
            'cookie': self.cookie,
            'server_id': self.server_id,
            'opencode_enabled': self.opencode_enabled,
            'deepseek_enabled': self.deepseek_enabled,
            'deepseek_token': self.deepseek_token
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log_config_save(self.workspace_id)
    
    def is_valid(self):
        """Check if configuration has valid values."""
        return bool(self.workspace_id and self.cookie and self.server_id)
    
    def deepseek_is_valid(self):
        """Check if DeepSeek balance display is enabled and has a token."""
        return self.deepseek_enabled and bool(self.deepseek_token)