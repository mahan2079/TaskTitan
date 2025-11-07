"""
Unit tests for utility functions.
"""

import pytest
import os
import tempfile
from app.utils.validators import (
    validate_text,
    validate_title,
    validate_description,
    validate_category,
    validate_tag,
    validate_priority,
    validate_date_string,
    validate_time_string,
    validate_file_path,
    validate_file_extension,
    validate_file_size,
    sanitize_filename,
    sanitize_category,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH
)
from app.utils.security import (
    sanitize_path,
    check_file_security,
    secure_file_copy,
    validate_attachment_file
)
from app.core.config import ConfigManager, get_config, set_config


class TestValidators:
    """Test cases for validation functions."""
    
    def test_validate_text_valid(self):
        """Test validating valid text."""
        valid, error = validate_text("Valid text", "test")
        assert valid is True
        assert error is None
    
    def test_validate_text_empty(self):
        """Test validating empty text."""
        valid, error = validate_text("", "test", allow_empty=False)
        assert valid is False
        assert error is not None
    
    def test_validate_text_too_long(self):
        """Test validating text that's too long."""
        long_text = "a" * (MAX_TITLE_LENGTH + 1)
        valid, error = validate_text(long_text, "test", max_length=MAX_TITLE_LENGTH)
        assert valid is False
        assert "exceed" in error.lower()
    
    def test_validate_title(self):
        """Test title validation."""
        valid, error = validate_title("My Title")
        assert valid is True
        
        valid, error = validate_title("")
        assert valid is False
    
    def test_validate_description(self):
        """Test description validation."""
        valid, error = validate_description("A description")
        assert valid is True
        
        # Description can be empty
        valid, error = validate_description("", allow_empty=True)
        assert valid is True
    
    def test_validate_category(self):
        """Test category validation."""
        valid, error = validate_category("Work")
        assert valid is True
        
        # Category with path separators should fail
        valid, error = validate_category("Work/Personal")
        assert valid is False
    
    def test_validate_tag(self):
        """Test tag validation."""
        valid, error = validate_tag("important")
        assert valid is True
        
        # Tag with comma should fail
        valid, error = validate_tag("important,urgent")
        assert valid is False
    
    def test_validate_priority(self):
        """Test priority validation."""
        valid, error = validate_priority(1)
        assert valid is True
        
        valid, error = validate_priority(5)
        assert valid is False
    
    def test_validate_date_string(self):
        """Test date string validation."""
        valid, error = validate_date_string("2024-01-01")
        assert valid is True
        
        valid, error = validate_date_string("01-01-2024")
        assert valid is False
        
        valid, error = validate_date_string("2024-13-01")  # Invalid month
        assert valid is False
    
    def test_validate_time_string(self):
        """Test time string validation."""
        valid, error = validate_time_string("09:00")
        assert valid is True
        
        valid, error = validate_time_string("09:00:00")
        assert valid is True
        
        valid, error = validate_time_string("25:00")
        assert valid is False
    
    def test_validate_file_path(self):
        """Test file path validation."""
        valid, error = validate_file_path("test.txt")
        assert valid is True
        
        # Path traversal attempt
        valid, error = validate_file_path("../../etc/passwd")
        assert valid is False
    
    def test_validate_file_extension(self):
        """Test file extension validation."""
        valid, error = validate_file_extension("test.pdf")
        assert valid is True
        
        valid, error = validate_file_extension("test.exe")
        assert valid is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        sanitized = sanitize_filename("test/file.txt")
        assert "/" not in sanitized
        
        sanitized = sanitize_filename("test<>file.txt")
        assert "<" not in sanitized and ">" not in sanitized
    
    def test_sanitize_category(self):
        """Test category sanitization."""
        sanitized = sanitize_category("Work/Personal")
        assert "/" not in sanitized


class TestSecurity:
    """Test cases for security functions."""
    
    def test_sanitize_path(self):
        """Test path sanitization."""
        sanitized = sanitize_path("test.txt")
        assert sanitized == "test.txt"
        
        sanitized = sanitize_path("../../etc/passwd")
        assert sanitized is None
    
    def test_check_file_security(self, temp_dir):
        """Test file security checking."""
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        safe, error = check_file_security(test_file)
        assert safe is True
        
        # Non-existent file
        safe, error = check_file_security(os.path.join(temp_dir, "nonexistent.txt"))
        assert safe is False
    
    def test_secure_file_copy(self, temp_dir):
        """Test secure file copying."""
        source = os.path.join(temp_dir, "source.txt")
        dest = os.path.join(temp_dir, "dest.txt")
        
        with open(source, 'w') as f:
            f.write("test content")
        
        success, error = secure_file_copy(source, dest)
        assert success is True
        assert os.path.exists(dest)


class TestConfigManager:
    """Test cases for configuration management."""
    
    def test_config_get_set(self, temp_config):
        """Test getting and setting config values."""
        manager = temp_config
        
        # Get default value
        width = manager.get('window.width')
        assert width == 1200
        
        # Set new value
        manager.set('window.width', 1400)
        width = manager.get('window.width')
        assert width == 1400
    
    def test_config_get_section(self, temp_config):
        """Test getting config section."""
        manager = temp_config
        window_config = manager.get_section('window')
        
        assert isinstance(window_config, dict)
        assert 'width' in window_config
    
    def test_config_update_section(self, temp_config):
        """Test updating config section."""
        manager = temp_config
        manager.update_section('window', {'width': 1500, 'height': 900})
        
        assert manager.get('window.width') == 1500
        assert manager.get('window.height') == 900
    
    def test_get_config_function(self, temp_config):
        """Test convenience get_config function."""
        width = get_config('window.width')
        assert width is not None
    
    def test_set_config_function(self, temp_config):
        """Test convenience set_config function."""
        set_config('window.width', 1600)
        width = get_config('window.width')
        assert width == 1600

