"""
Search Results Widget for TaskTitan.

Displays search results in a dropdown-style widget.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.controllers.search_manager import SearchResult
from app.resources import get_icon


class SearchResultItem(QWidget):
    """Widget for displaying a single search result."""
    
    clicked = pyqtSignal(SearchResult)
    
    def __init__(self, result: SearchResult, parent=None):
        """Initialize the search result item."""
        super().__init__(parent)
        self.result = result
        
        self.setupUI()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def setupUI(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Icon based on type
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.result.item_type == 'task':
            icon_label.setText("✓")
            icon_label.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")
        elif self.result.item_type == 'event':
            icon_label.setText("📅")
            icon_label.setStyleSheet("font-size: 16px;")
        elif self.result.item_type == 'habit':
            icon_label.setText("↻")
            icon_label.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
        elif self.result.item_type == 'goal':
            icon_label.setText("🎯")
            icon_label.setStyleSheet("font-size: 16px;")
        else:  # category
            icon_label.setText("📁")
            icon_label.setStyleSheet("font-size: 16px;")
        
        layout.addWidget(icon_label)
        
        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(self.result.title)
        title_label.setWordWrap(False)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        text_layout.addWidget(title_label)
        
        # Description
        if self.result.description:
            desc_label = QLabel(self.result.description)
            desc_label.setWordWrap(False)
            desc_label.setStyleSheet("color: #6B7280; font-size: 11px;")
            text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout, 1)
        
        # Type badge
        type_label = QLabel(self.result.item_type.capitalize())
        type_label.setStyleSheet("""
            background-color: #F3F4F6;
            color: #374151;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        layout.addWidget(type_label)
        
        self.setMinimumHeight(60)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.result)


class SearchResultsWidget(QWidget):
    """Widget for displaying search results."""
    
    resultSelected = pyqtSignal(SearchResult)
    
    def __init__(self, parent=None):
        """Initialize the search results widget."""
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setupUI()
        self.hide()
    
    def setupUI(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container frame
        container = QFrame()
        container.setObjectName("searchResultsContainer")
        from app.themes import ThemeManager
        theme_colors = ThemeManager.get_current_palette()
        
        container.setStyleSheet(f"""
            QFrame#searchResultsContainer {{
                background-color: {theme_colors.get('surface', '#FFFFFF')};
                border: 1px solid {theme_colors.get('border', '#E2E8F0')};
                border-radius: 8px;
                max-height: 400px;
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setObjectName("searchResultsList")
        self.results_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Style the list
        self.results_list.setStyleSheet("""
            QListWidget#searchResultsList {
                border: none;
                background: transparent;
            }
            QListWidget#searchResultsList::item {
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
            QListWidget#searchResultsList::item:last {
                border-bottom: none;
            }
            QListWidget#searchResultsList::item:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QListWidget#searchResultsList::item:selected {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        
        self.results_list.itemClicked.connect(self.onItemClicked)
        container_layout.addWidget(self.results_list)
        
        # Empty state
        self.empty_label = QLabel("No results found")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #9CA3AF; padding: 20px;")
        self.empty_label.hide()
        container_layout.addWidget(self.empty_label)
        
        layout.addWidget(container)
        
        self.setMaximumWidth(500)
        self.setMaximumHeight(400)
    
    def setResults(self, results):
        """Set search results to display."""
        self.results_list.clear()
        
        if not results:
            self.empty_label.show()
            self.results_list.hide()
            return
        
        self.empty_label.hide()
        self.results_list.show()
        
        for result in results:
            item_widget = SearchResultItem(result)
            item_widget.clicked.connect(self.resultSelected.emit)
            
            list_item = QListWidgetItem(self.results_list)
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, result)
            
            self.results_list.setItemWidget(list_item, item_widget)
        
        # Select first item
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def onItemClicked(self, item):
        """Handle item click."""
        result = item.data(Qt.ItemDataRole.UserRole)
        if result:
            self.resultSelected.emit(result)
    
    def getSelectedResult(self):
        """Get the currently selected result."""
        current_item = self.results_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def selectNext(self):
        """Select the next result."""
        if self.results_list.count() == 0:
            return
        
        current_row = self.results_list.currentRow()
        next_row = (current_row + 1) % self.results_list.count()
        self.results_list.setCurrentRow(next_row)
    
    def selectPrevious(self):
        """Select the previous result."""
        if self.results_list.count() == 0:
            return
        
        current_row = self.results_list.currentRow()
        prev_row = (current_row - 1) % self.results_list.count()
        self.results_list.setCurrentRow(prev_row)

