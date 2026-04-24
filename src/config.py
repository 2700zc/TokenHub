"""
Configuration manager for TokenHub.
Handles workspace_id and cookie persistence in config.json.
"""

import json
import os

try:
    from .logger import log_config_load, log_config_save
except ImportError:
    from logger import log_config_load, log_config_save

class Config:
    """Configuration manager for TokenHub."""
    
    CONFIG_FILE = 'config.json'
    
    def __init__(self):
        self.workspace_id = ""
        self.cookie = ""
        self.server_id = ""
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
        except (json.JSONDecodeError, Exception):
            # Corrupted file - reset to default
            self.workspace_id = ""
            self.cookie = ""
            self.server_id = ""
            self.save()
    
    def save(self):
        """Save configuration to JSON file."""
        data = {
            'workspace_id': self.workspace_id,
            'cookie': self.cookie,
            'server_id': self.server_id
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log_config_save(self.workspace_id)
    
    def is_valid(self):
        """Check if configuration has valid values."""
        return bool(self.workspace_id and self.cookie and self.server_id)