import sys
import os
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication, QDialog

from app.views.main_window import TaskTitanApp
from app.resources import get_resource_path, APP_NAME, APP_VERSION
from app.utils.migrate_db import migrate_databases
from app.utils.logger import setup_logging, get_logger
from app.utils.error_handler import GlobalExceptionHandler

logger = get_logger(__name__)

def main():
    """Main entry point for the modernized TaskTitan application."""
    # Setup logging first
    setup_logging()
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    app = QApplication(sys.argv)
    
    # Install global exception handler
    error_handler = GlobalExceptionHandler(app)
    
    try:
        # Migrate any existing databases to the central location
        logger.info("Migrating databases...")
        migrate_databases()
        
        # Apply previously saved theme (or system auto) at startup
        try:
            from app.themes import ThemeManager
            # Apply theme once before UI is created (base palette)
            ThemeManager.apply_saved_theme(app)
            logger.debug("Theme applied successfully")
        except Exception as e:
            logger.warning(f"Theme apply failed, using fallback: {e}")
        
        # Initialize authentication
        from app.auth.authentication import get_auth_manager
        auth_manager = get_auth_manager()
        
        # Show login dialog if not authenticated
        if not auth_manager.is_authenticated():
            from app.views.login_dialog import LoginDialog
            logger.info("Showing login dialog...")
            login_dialog = LoginDialog(allow_creation=True)
            
            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                logger.info("Login cancelled, exiting application")
                sys.exit(0)
            
            logger.info("User authenticated successfully")
        
        # Create and show the main application window
        logger.info("Creating main window...")
        window = TaskTitanApp()
        window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        window.show()
        
        # Re-apply after UI creation to normalize/clear inline styles on widgets
        try:
            from app.themes import ThemeManager
            ThemeManager.apply_saved_theme(app)
        except Exception as e:
            logger.debug(f"Error re-applying theme: {e}")
        
        # Set up async event loop for smoother UI and animations
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        logger.info("Application started successfully")
        
        # Initialize backup manager for automatic backups
        try:
            from app.utils.backup_manager import BackupManager
            backup_manager = BackupManager()
            # Auto-backup will be started if enabled in config
            logger.debug("Backup manager initialized")
        except Exception as e:
            logger.warning(f"Could not initialize backup manager: {e}")
        
        # Run the application
        with loop:
            sys.exit(loop.run_forever())
            
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 