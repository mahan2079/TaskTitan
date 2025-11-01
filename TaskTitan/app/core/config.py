"""
Centralized configuration management for TaskTitan.

This module provides a unified configuration system with support for
JSON-based config files, environment variables, and runtime updates.
"""

import json
import os
import sys
import base64
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.utils.logger import get_logger
from app.resources.constants import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_SIDEBAR_WIDTH,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    POMODORO_WORK_MINUTES,
    POMODORO_SHORT_BREAK_MINUTES,
    POMODORO_LONG_BREAK_MINUTES,
    POMODORO_LONG_BREAK_INTERVAL
)

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration."""
    
    _instance: Optional['ConfigManager'] = None
    _initialized = False
    
    def __init__(self):
        """Initialize the configuration manager."""
        if ConfigManager._initialized:
            return
        
        self.config: Dict[str, Any] = {}
        self.config_file = self._get_config_path()
        self._load_config()
        
        ConfigManager._initialized = True
    
    def _get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_dir = Path(os.path.dirname(sys.executable))
        else:
            # Running as script
            base_dir = Path(__file__).parent.parent.parent
        
        # Use data directory for config
        data_dir = base_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        return data_dir / 'config.json'
    
    def _get_secure_config_path(self) -> Path:
        """Get the path to the secure (encrypted) configuration file."""
        config_dir = self.config_file.parent
        return config_dir / 'secure_config.enc'
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Get encryption key for secure config storage.
        Derives key from user's authentication or system identifier.
        
        Returns:
            Encryption key bytes or None if not available
        """
        try:
            # Try to get encryption key from user password or system
            from app.auth.authentication import get_auth_manager
            auth_manager = get_auth_manager()
            
            # Use a system identifier if user not authenticated
            if auth_manager.is_authenticated():
                user = auth_manager.get_current_user()
                if user:
                    # Use username as part of key derivation
                    password = user.get('username', 'tasktitan')
                else:
                    password = 'tasktitan'
            else:
                # Use system identifier
                import platform
                password = f"tasktitan_{platform.node()}"
            
            # Derive key using PBKDF2
            salt = b'tasktitan_salt_2024'  # In production, store salt securely
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return key
            
        except Exception as e:
            logger.warning(f"Could not derive encryption key: {e}")
            return None
    
    def _encrypt_value(self, value: str) -> Optional[str]:
        """
        Encrypt a sensitive value.
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value (base64) or None if encryption failed
        """
        try:
            key = self._get_encryption_key()
            if not key:
                return None
            
            fernet = Fernet(key)
            encrypted = fernet.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting value: {e}", exc_info=True)
            return None
    
    def _decrypt_value(self, encrypted_value: str) -> Optional[str]:
        """
        Decrypt a sensitive value.
        
        Args:
            encrypted_value: Encrypted value (base64)
            
        Returns:
            Decrypted value or None if decryption failed
        """
        try:
            key = self._get_encryption_key()
            if not key:
                return None
            
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting value: {e}", exc_info=True)
            return None
    
    def set_secure(self, key_path: str, value: str, save: bool = True):
        """
        Set a secure (encrypted) configuration value.
        
        Args:
            key_path: Path to the config key (e.g., 'ai.openai_api_key')
            value: Value to encrypt and store
            save: Whether to save immediately
        """
        encrypted_value = self._encrypt_value(value)
        if encrypted_value:
            # Store encrypted value in secure config
            self.set(key_path, f"ENC:{encrypted_value}", save)
            logger.debug(f"Set secure config {key_path}")
        else:
            logger.warning(f"Failed to encrypt value for {key_path}")
    
    def get_secure(self, key_path: str, default: Any = None) -> Optional[str]:
        """
        Get a secure (decrypted) configuration value.
        
        Args:
            key_path: Path to the config key
            default: Default value if not found
            
        Returns:
            Decrypted value or default
        """
        value = self.get(key_path, default)
        
        if isinstance(value, str) and value.startswith("ENC:"):
            encrypted_value = value[4:]  # Remove "ENC:" prefix
            decrypted = self._decrypt_value(encrypted_value)
            return decrypted if decrypted else default
        
        return value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'window': {
                'width': DEFAULT_WINDOW_WIDTH,
                'height': DEFAULT_WINDOW_HEIGHT,
                'sidebar_width': DEFAULT_SIDEBAR_WIDTH,
                'remember_size': True,
                'remember_position': True
            },
            'display': {
                'font_family': DEFAULT_FONT_FAMILY,
                'font_size': DEFAULT_FONT_SIZE,
                'theme': 'System (Auto)',
                'follow_system_theme': True
            },
            'pomodoro': {
                'work_minutes': POMODORO_WORK_MINUTES,
                'short_break_minutes': POMODORO_SHORT_BREAK_MINUTES,
                'long_break_minutes': POMODORO_LONG_BREAK_MINUTES,
                'long_break_interval': POMODORO_LONG_BREAK_INTERVAL,
                'auto_start_breaks': False,
                'auto_start_work': False
            },
            'backup': {
                'auto_backup_enabled': False,
                'auto_backup_interval': 'daily',  # daily, weekly, monthly
                'backup_retention_days': 30,
                'backup_location': None  # None = use default
            },
            'files': {
                'max_file_size_mb': 50,
                'allowed_extensions': [
                    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
                    '.zip', '.rar', '.7z', '.tar', '.gz',
                    '.xls', '.xlsx', '.csv', '.ods',
                    '.ppt', '.pptx', '.odp',
                    '.mp3', '.wav', '.ogg', '.flac',
                    '.mp4', '.avi', '.mov', '.mkv', '.webm',
                    '.json', '.xml', '.html', '.md'
                ]
            },
            'notifications': {
                'enabled': True,
                'task_reminders': True,
                'deadline_alerts': True,
                'backup_notifications': True
            },
            'updates': {
                'check_for_updates': False,
                'check_interval_days': 7
            },
            'database': {
                'backup_on_startup': False,
                'integrity_check_on_startup': False
            },
            'performance': {
                'cache_enabled': True,
                'cache_size_mb': 100,
                'lazy_loading': True
            },
            'ai': {
                'provider': 'openai',  # openai, anthropic, local
                'openai_api_key': None,  # Stored encrypted
                'anthropic_api_key': None,  # Stored encrypted
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 1000
            }
        }
    
    def _load_config(self):
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self.config = self._merge_config(self._get_default_config(), file_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            else:
                self.config = self._get_default_config()
                self._save_config()
                logger.info("Created default configuration file")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.config = self._get_default_config()
    
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults."""
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key_path: Path to the config key (e.g., 'window.width')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """
        Set a configuration value using dot notation.
        
        Args:
            key_path: Path to the config key (e.g., 'window.width')
            value: Value to set
            save: Whether to save to file immediately
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent dict
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        if save:
            self._save_config()
        
        logger.debug(f"Set config {key_path} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: Section name (e.g., 'window')
            
        Returns:
            Configuration section dictionary
        """
        return self.config.get(section, {})
    
    def update_section(self, section: str, values: Dict[str, Any], save: bool = True):
        """
        Update a configuration section.
        
        Args:
            section: Section name
            values: Dictionary of values to update
            save: Whether to save to file immediately
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section].update(values)
        
        if save:
            self._save_config()
        
        logger.debug(f"Updated config section {section}")
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self._get_default_config()
        self._save_config()
        logger.info("Reset configuration to defaults")
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get singleton instance of ConfigManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_config(key_path: str = None, default: Any = None) -> Any:
    """
    Get a configuration value (convenience function).
    
    Args:
        key_path: Path to the config key (e.g., 'window.width')
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    manager = ConfigManager.get_instance()
    if key_path:
        return manager.get(key_path, default)
    return manager.config


def set_config(key_path: str, value: Any, save: bool = True):
    """
    Set a configuration value (convenience function).
    
    Args:
        key_path: Path to the config key
        value: Value to set
        save: Whether to save to file immediately
    """
    ConfigManager.get_instance().set(key_path, value, save)

