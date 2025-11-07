"""
Update checker for TaskTitan.

This module checks for application updates and notifies users
when new versions are available.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from app.utils.logger import get_logger
from app.core.config import get_config, set_config
from app.resources.constants import APP_VERSION

logger = get_logger(__name__)


class UpdateChecker(QObject):
    """Checks for application updates."""
    
    update_available = pyqtSignal(str, str)  # Emits (version, download_url)
    check_completed = pyqtSignal(bool)  # Emits success status
    
    def __init__(self, parent=None):
        """Initialize update checker."""
        super().__init__(parent)
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_for_updates)
        self.last_check = None
        self._setup_auto_check()
    
    def _setup_auto_check(self):
        """Setup automatic update checking."""
        enabled = get_config('updates.check_for_updates', False)
        if enabled:
            interval_days = get_config('updates.check_interval_days', 7)
            interval_ms = interval_days * 24 * 60 * 60 * 1000  # Convert to milliseconds
            self.check_timer.start(interval_ms)
            logger.info(f"Auto-update check enabled (interval: {interval_days} days)")
    
    def check_for_updates(self, force: bool = False) -> Tuple[bool, Optional[Dict]]:
        """
        Check for available updates.
        
        Args:
            force: Force check even if recently checked
            
        Returns:
            Tuple of (success, update_info_dict)
        """
        try:
            # Check if we should skip (recently checked)
            if not force:
                last_check_str = get_config('updates.last_check', None)
                if last_check_str:
                    try:
                        last_check = datetime.fromisoformat(last_check_str)
                        if datetime.now() - last_check < timedelta(hours=1):
                            logger.debug("Skipping update check (recently checked)")
                            return True, None
                    except Exception:
                        pass
            
            # Update API endpoint (can be configured)
            update_url = get_config('updates.update_url', 'https://api.github.com/repos/yourusername/tasktitan/releases/latest')
            
            # Make request
            try:
                with urllib.request.urlopen(update_url, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    
                    # Extract version info
                    latest_version = data.get('tag_name', '').lstrip('v')
                    download_url = None
                    
                    # Find download URL
                    assets = data.get('assets', [])
                    if assets:
                        # Look for Windows executable
                        for asset in assets:
                            if asset.get('name', '').endswith('.exe'):
                                download_url = asset.get('browser_download_url')
                                break
                    
                    # Compare versions
                    if self._compare_versions(latest_version, APP_VERSION):
                        update_info = {
                            'version': latest_version,
                            'download_url': download_url or data.get('html_url', ''),
                            'release_notes': data.get('body', ''),
                            'release_date': data.get('published_at', '')
                        }
                        
                        # Save last check time
                        set_config('updates.last_check', datetime.now().isoformat())
                        self.last_check = datetime.now()
                        
                        logger.info(f"Update available: {latest_version}")
                        self.update_available.emit(latest_version, update_info.get('download_url', ''))
                        self.check_completed.emit(True)
                        
                        return True, update_info
                    else:
                        logger.debug(f"No update available (current: {APP_VERSION}, latest: {latest_version})")
                        set_config('updates.last_check', datetime.now().isoformat())
                        self.check_completed.emit(True)
                        return True, None
                        
            except urllib.error.URLError as e:
                logger.warning(f"Could not check for updates: {e}")
                self.check_completed.emit(False)
                return False, None
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            self.check_completed.emit(False)
            return False, None
    
    def _compare_versions(self, version1: str, version2: str) -> bool:
        """
        Compare two version strings.
        
        Returns:
            True if version1 > version2
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except Exception:
            # Fallback to string comparison
            return version1 > version2


class UpdateDialog(QDialog):
    """Dialog for displaying update information."""
    
    def __init__(self, update_info: Dict, parent=None):
        """Initialize update dialog."""
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("Update Available")
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"TaskTitan {self.update_info['version']} is available!")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Release notes
        notes_label = QLabel("Release Notes:")
        layout.addWidget(notes_label)
        
        notes_text = QTextEdit()
        notes_text.setPlainText(self.update_info.get('release_notes', 'No release notes available.'))
        notes_text.setReadOnly(True)
        notes_text.setMaximumHeight(200)
        layout.addWidget(notes_text)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        download_btn = QPushButton("Download Update")
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        later_btn = QPushButton("Remind Me Later")
        later_btn.clicked.connect(self.accept)
        button_layout.addWidget(later_btn)
        
        layout.addLayout(button_layout)
    
    def download_update(self):
        """Open download URL."""
        import webbrowser
        url = self.update_info.get('download_url', '')
        if url:
            webbrowser.open(url)
        self.accept()

