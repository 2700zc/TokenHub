"""
Windows theme detection and color palette manager.
Detects if Windows is using dark or light theme via registry.
"""

import winreg
import platform

class ThemeManager:
    """Windows theme detection and color palette manager."""
    
    # Dark mode colors
    DARK_COLORS = {
        'bg': '#1e1e1e',
        'fg': '#ffffff',
        'accent': '#4fc1ff'
    }
    
    # Light mode colors
    LIGHT_COLORS = {
        'bg': '#f3f3f3',
        'fg': '#000000',
        'accent': '#0078d4'
    }
    
    def __init__(self):
        self.is_dark = self._detect_dark_theme()
        self._colors = self.DARK_COLORS if self.is_dark else self.LIGHT_COLORS
    
    def _detect_dark_theme(self) -> bool:
        """Detect if Windows is using dark theme.
        
        Reads from registry:
        HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize
        Key: AppsUseLightTheme (0 = dark, 1 = light)
        """
        # Only works on Windows
        if platform.system() != 'Windows':
            return False
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            # AppsUseLightTheme: 0 = dark, 1 = light
            return value == 0
        except Exception:
            # Default to light theme if detection fails
            return False
    
    def get_colors(self) -> dict:
        """Get current theme colors as dictionary."""
        return self._colors
    
    def get_bg(self) -> str:
        """Get background color."""
        return self._colors['bg']
    
    def get_fg(self) -> str:
        """Get foreground (text) color."""
        return self._colors['fg']
    
    def get_accent(self) -> str:
        """Get accent color."""
        return self._colors['accent']