from __future__ import annotations

import os
from typing import Dict, Callable, Tuple

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

import darkdetect


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _hex(v: str) -> str:
    v = v.strip()
    return v if v.startswith("#") else f"#{v}"


def _clamp(n: int) -> int:
    return max(0, min(255, n))


def _adjust(c: str, factor: float) -> str:
    """Lighten (>1) or darken (<1) a hex color."""
    c = c.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r = _clamp(int(r * factor))
    g = _clamp(int(g * factor))
    b = _clamp(int(b * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def build_theme_qss(p: Dict[str, str]) -> str:
    bg = _hex(p["bg"])              # window background
    surface = _hex(p["surface"])    # cards/input background
    surface2 = _hex(p.get("surface2", p["surface"]))
    text = _hex(p["text"])          # primary text
    muted = _hex(p["muted"])        # secondary text
    border = _hex(p["border"])      # borders
    primary = _hex(p["primary"])    # primary brand
    accent = _hex(p["accent"])      # secondary accent
    button_text = _hex(p["button_text"])  # text on primary buttons
    selection = _hex(p["selection"])     # selection background
    selection_text = _hex(p["selection_text"])  # text on selection

    hover = _hex(p.get("hover", _adjust(primary, 1.1)))
    press = _hex(p.get("press", _adjust(primary, 0.9)))
    
    # Additional derived colors
    error = _hex(p.get("error", "#EF4444"))
    error_bg = _hex(p.get("error_bg", _adjust(error, 0.1)))
    warning = _hex(p.get("warning", "#F59E0B"))
    success = _hex(p.get("success", "#10B981"))

    return f"""
    /* Base */
    QMainWindow, QDialog {{
      background-color: {bg};
      color: {text};
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 14px;
    }}
    QWidget {{
      background-color: {bg};
      color: {text};
    }}
    
    /* Labels - transparent background to blend with parent */
    QLabel {{
      background-color: transparent;
      color: {text};
    }}

    /* Toolbar */
    QToolBar {{
      background: {surface};
      border-bottom: 1px solid {border};
      spacing: 10px;
    }}
    QToolButton {{ background: transparent; color: {text}; border: none; border-radius: 6px; padding: 6px; }}
    QToolButton:hover {{ background: {surface2}; }}

    /* Buttons */
    QPushButton {{
      background-color: {primary};
      color: {button_text};
      border: none;
      border-radius: 8px;
      padding: 8px 14px;
      font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {hover}; }}
    QPushButton:pressed {{ background-color: {press}; }}
    QPushButton:disabled {{ background-color: {_adjust(primary, 0.6)}; color: {_adjust(button_text, 1.1)}; }}

    /* Inputs - transparent background to blend with parent container */
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {{
      background-color: transparent;
      color: {text};
      border: 1px solid {border};
      border-radius: 6px;
      padding: 8px 10px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
      border: 1px solid {primary};
      background-color: transparent;
    }}
    QComboBox QAbstractItemView {{
      background: {surface};
      color: {text};
      border: 1px solid {border};
      selection-background-color: {selection};
      selection-color: {selection_text};
    }}
    QComboBox::drop-down {{
      background-color: transparent;
      border: none;
    }}

    /* Menus */
    QMenuBar {{ background: {surface}; color: {text}; border: none; }}
    QMenuBar::item:selected {{ background: {surface2}; }}
    QMenu {{ background: {surface}; color: {text}; border: 1px solid {border}; border-radius: 6px; }}
    QMenu::item:selected {{ background: {selection}; color: {selection_text}; }}

    /* Tabs */
    QTabWidget::pane {{ border: 1px solid {border}; border-radius: 8px; top: -1px; background: {surface}; }}
    QTabBar::tab {{ background: {surface2}; color: {muted}; padding: 8px 14px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }}
    QTabBar::tab:selected {{ background: {primary}; color: {button_text}; }}
    QTabBar::tab:hover:!selected {{ background: {surface}; color: {text}; }}

    /* Lists & Tables */
    QTableView, QTreeView, QListView {{
      background: {surface};
      color: {text};
      border: 1px solid {border};
      border-radius: 8px;
      selection-background-color: {selection};
      selection-color: {selection_text};
      gridline-color: {border};
      alternate-background-color: {surface2};
    }}
    QHeaderView::section {{ background: {surface2}; color: {text}; padding: 8px; border: none; font-weight: 600; }}

    /* Containers */
    QGroupBox {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; margin-top: 12px; }}
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; background-color: transparent; color: {text}; }}
    QScrollArea {{ background: {bg}; border: none; }}
    QStackedWidget {{ background: {bg}; }}

    /* Progress */
    QProgressBar {{ background: {surface2}; color: {text}; border: none; border-radius: 8px; text-align: center; }}
    QProgressBar::chunk {{ background: {primary}; border-radius: 8px; }}

    /* Check / Radio */
    QCheckBox, QRadioButton {{ 
        color: {text}; 
        spacing: 8px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{ 
        width: 20px; 
        height: 20px; 
        border: 2px solid {border}; 
        border-radius: 4px; 
        background: {surface}; 
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{ 
        background: {primary}; 
        border-color: {primary}; 
        image: none;
    }}
    QCheckBox::indicator:checked:disabled {{ 
        background: {muted}; 
        border-color: {muted}; 
    }}
    QCheckBox::indicator:hover {{
        border-color: {primary};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{ background: {surface2}; width: 12px; margin: 0; border-radius: 6px; }}
    QScrollBar::handle:vertical {{ background: {border}; min-height: 20px; border-radius: 6px; }}
    QScrollBar::handle:vertical:hover {{ background: {primary}; }}
    QScrollBar:horizontal {{ background: {surface2}; height: 12px; margin: 0; border-radius: 6px; }}
    QScrollBar::handle:horizontal {{ background: {border}; min-width: 20px; border-radius: 6px; }}
    QScrollBar::handle:horizontal:hover {{ background: {primary}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ height: 0; width: 0; }}

    /* Calendar */
    QCalendarWidget {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; color: {text}; }}
    QCalendarWidget QToolButton {{ background: {primary}; color: {button_text}; border-radius: 6px; padding: 6px; font-weight: 600; }}
    QCalendarWidget QToolButton:hover {{ background: {hover}; }}
    QCalendarWidget QAbstractItemView {{ background: {surface}; selection-background-color: {selection}; selection-color: {selection_text}; color: {text}; gridline-color: {border}; }}

    /* Frames / Cards via properties */
    QFrame {{ background: {bg}; }}
    *[data-card="true"] {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; padding: 16px; }}
    /* Activity widgets */
    *[data-activity="true"][data-completed="true"] {{ opacity: 0.92; }}
    *[data-activity="true"] QLabel#activityTitle {{ background-color: transparent; color: {text}; }}
    *[data-activity="true"][data-completed="true"] QLabel#activityTitle {{ background-color: transparent; color: {muted}; text-decoration: line-through; }}
    /* Activity type color bars */
    QFrame[data-activity-type="task"] {{ background: #ef4444; border-radius: 2px; }}
    QFrame[data-activity-type="event"] {{ background: {primary}; border-radius: 2px; }}
    QFrame[data-activity-type="habit"] {{ background: #10b981; border-radius: 2px; }}

    /* Sidebar */
    QWidget#sidebar {{ background: {surface}; border-right: 1px solid {border}; }}
    QWidget#sidebar QPushButton {{
      background: transparent;
      color: {text};
      border: none;
      text-align: left;
      padding: 10px 12px;
      border-radius: 8px;
    }}
    QWidget#sidebar QPushButton:hover {{ background: {surface2}; }}
    QWidget#sidebar QPushButton[data-selected="true"] {{ background: {primary}; color: {button_text}; }}
    QWidget#sidebar QLabel {{
      background-color: transparent;
      color: {text};
    }}

    /* Header bar */
    QWidget#headerBar {{ background: {surface}; border-bottom: 1px solid {border}; }}
    QLabel#headerTitle {{ background-color: transparent; color: {text}; font-size: 18px; font-weight: 600; }}
    QLineEdit#headerSearch {{ background-color: transparent; border: 1px solid {border}; border-radius: 6px; padding: 6px 10px; color: {text}; }}
    
    /* Navigation controls */
    QWidget#navControlsContainer {{
      background-color: transparent;
    }}
    QWidget#dailyNavContainer {{
      background-color: transparent;
    }}
    QWidget#weeklyNavContainer {{
      background-color: transparent;
    }}
    QPushButton#navButton {{
      background-color: {surface2};
      color: {text};
      border: 1px solid {border};
      border-radius: 8px;
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 500;
      min-width: 100px;
    }}
    QPushButton#navButton:hover {{
      background-color: {hover};
      border-color: {primary};
    }}
    QPushButton#navButton:pressed {{
      background-color: {press};
    }}
    QLabel#dailyDayLabel {{
      background-color: transparent;
      color: {text};
      font-size: 16px;
      font-weight: 600;
      padding: 8px 16px;
    }}
    QLabel#weeklyWeekLabel {{
      background-color: transparent;
      color: {text};
      font-size: 16px;
      font-weight: 600;
      padding: 8px 16px;
    }}

    /* Weekly plan */
    QWidget#weeklyHeader {{ background: {surface}; border: 1px solid {border}; border-radius: 10px; }}
    QLabel#weeklyWeekLabel {{ background-color: transparent; color: {text}; font-size: 18px; font-weight: 600; }}
    QLabel#weeklyStatus {{ background-color: transparent; color: {muted}; font-style: italic; }}
    QGraphicsView {{ background: {bg}; border: 1px solid {border}; border-radius: 8px; }}
    
    /* Dialog components */
    QDialog {{
      background-color: {bg};
      color: {text};
    }}
    QDialog QLabel {{
      background-color: transparent;
      color: {text};
    }}
    QDialog QFrame {{
      background-color: {bg};
      color: {text};
    }}
    QDialog QFrame[data-card="true"] {{
      background-color: {surface};
      border: 1px solid {border};
      border-radius: 12px;
      padding: 16px;
    }}
    QDialog QFrame#detailsItem {{
      background-color: {surface2};
      border-radius: 6px;
      padding: 10px;
      border: 1px solid {border};
    }}
    QDialog QLabel#title {{
      background-color: transparent;
      color: {text};
      font-size: 18px;
      font-weight: bold;
    }}
    QDialog QLabel#subtitle {{
      background-color: transparent;
      color: {muted};
      font-size: 16px;
      font-weight: bold;
    }}
    QDialog QLabel#sectionHeader {{
      background-color: transparent;
      color: {text};
      font-size: 16px;
      font-weight: bold;
    }}
    QDialog QPushButton#primaryBtn {{
      background-color: {primary};
      color: {button_text};
      border: none;
    }}
    QDialog QPushButton#primaryBtn:hover {{
      background-color: {hover};
    }}
    QDialog QPushButton#deleteBtn {{
      background-color: {error_bg};
      color: {error};
      border: 1px solid {error};
    }}
    QDialog QPushButton#deleteBtn:hover {{
      background-color: {error};
      color: {button_text};
    }}
    
    /* Template components */
    QComboBox#templateCombo {{
      background-color: transparent;
      color: {text};
      border: 1px solid {border};
      border-radius: 6px;
      padding: 8px 10px;
    }}
    QComboBox#templateCombo:hover {{
      border-color: {primary};
    }}
    QComboBox#templateCombo:focus {{
      border-color: {primary};
    }}
    QPushButton#templateApplyBtn, QPushButton#templateSaveBtn {{
      background-color: {surface};
      color: {text};
      border: 1px solid {border};
      border-radius: 6px;
      padding: 8px 14px;
    }}
    QPushButton#templateApplyBtn:hover, QPushButton#templateSaveBtn:hover {{
      background-color: {surface2};
      border-color: {primary};
    }}
    
    /* Filter menu */
    QMenu#filterMenu {{
      background-color: {surface};
      border: 1px solid {border};
      border-radius: 6px;
      padding: 5px;
    }}
    QMenu#filterMenu::item {{
      padding: 6px 25px 6px 6px;
      border-radius: 4px;
    }}
    QMenu#filterMenu::item:selected {{
      background-color: {selection};
      color: {selection_text};
    }}
    
    /* Activity header */
    QWidget#activitiesHeader {{
      background-color: {surface};
      border-top-left-radius: 12px;
      border-top-right-radius: 12px;
    }}
    QLabel#activitiesTitle {{
      background-color: transparent;
      color: {text};
    }}
    QLabel#activitiesSubtitle {{
      background-color: transparent;
      color: {muted};
    }}
    QPushButton#filterButton {{
      background-color: {surface2};
      border: 2px solid {border};
      border-radius: 12px;
    }}
    QPushButton#filterButton:hover {{
      background-color: {surface};
      border-color: {primary};
    }}
    QPushButton#addActivityButton {{
      background-color: {primary};
      color: {button_text};
      border: none;
      border-radius: 12px;
      padding: 16px 32px;
      font-weight: bold;
    }}
    QPushButton#addActivityButton:hover {{
      background-color: {hover};
    }}
    QPushButton#addActivityButton:pressed {{
      background-color: {press};
    }}
    QFrame#activitiesSeparator {{
      background-color: {border};
    }}
    QScrollArea#activitiesScrollArea {{
      background-color: {bg};
    }}
    QWidget#activitiesContainer {{
      background-color: {bg};
    }}
    
    /* Empty state */
    QLabel#emptyState {{
      background-color: transparent;
      color: {muted};
    }}
    
    /* Calendar date picker dialog */
    QDialog QCalendarWidget {{
      background-color: {surface};
      border: 1px solid {border};
      border-radius: 8px;
      color: {text};
    }}
    
    /* Goal dialogs */
    QDialog QLineEdit, QDialog QDateEdit, QDialog QTimeEdit, QDialog QComboBox {{
      background-color: transparent;
      border: 1px solid {border};
      border-radius: 4px;
      padding: 6px;
      color: {text};
    }}
    QDialog QLineEdit:focus, QDialog QDateEdit:focus, QDialog QTimeEdit:focus, QDialog QComboBox:focus {{
      border-color: {primary};
    }}
    QDialog QDialogButtonBox {{
      background-color: {surface};
      border-top: 1px solid {border};
      padding: 10px;
    }}
    
    /* Custom progress charts */
    QWidget[data-chart="true"] {{
      background-color: {surface};
      border-radius: 8px;
    }}
    
    /* Productivity view */
    QWidget#productivityHeader {{
      background: {surface};
      border-bottom: 1px solid {border};
    }}
    QLabel#productivityTitle {{
      background-color: transparent;
      color: {text};
      font-size: 18px;
      font-weight: 600;
    }}
    QFrame[data-productivity-card="true"] {{
      background: {surface};
      border: 1px solid {border};
      border-radius: 12px;
      padding: 16px;
    }}
    QLabel#trackingTime {{
      background-color: transparent;
      color: {primary};
      font-size: 48px;
      font-weight: bold;
    }}
    QPushButton#stopBtn {{
      background-color: {error};
      color: {button_text};
    }}
    QPushButton#pauseBtn {{
      background-color: {warning};
      color: {button_text};
    }}
    QTableWidget {{
      background: {surface};
      border: 1px solid {border};
      border-radius: 8px;
      gridline-color: {border};
    }}
    QTableWidget::item:selected {{
      background-color: {selection};
      color: {selection_text};
    }}
    QTableWidget::item:alternate {{
      background-color: {surface2};
    }}
    
    /* Pomodoro widget */
    QLabel#pomodoroTitle {{
      background-color: transparent;
      color: {text};
    }}
    QLabel#pomodoroStateLabel {{
      background-color: transparent;
      color: {text};
    }}
    QLabel#pomodoroTimeDisplay {{
      background-color: transparent;
      color: {text};
    }}
    QWidget#pomodoroHeader {{
      background: {surface};
      border-bottom: 1px solid {border};
    }}
    QWidget#pomodoroHeader QLabel {{
      background-color: transparent;
      color: {text};
    }}
    
    /* Daily Tracker */
    QWidget#dailyTrackerHeader {{
      background: {surface};
      border-bottom: 1px solid {border};
    }}
    QLabel#dailyTrackerTitle {{
      background-color: transparent;
      color: {text};
    }}
    QWidget#dailyTrackerHeader QLabel {{
      background-color: transparent;
      color: {text};
    }}
    
    """


class ThemeManager:
    """Centralized theme management for TaskTitan with consistent QSS generator.

    All themes share the same component coverage; only palettes differ.
    """

    _THEMES: Dict[str, Callable[[], str]] = {}
    _PALETTES: Dict[str, Dict[str, str]] = {}

    @classmethod
    def _init_registry(cls) -> None:
        if cls._THEMES:
            return

        # Palettes (high-contrast and accessible)
        # Rewritten Light palette with higher contrast and distinct look
        light = {
            "bg": "#FAFAFA",
            "surface": "#FFFFFF",
            "surface2": "#F2F4F7",
            "text": "#0F172A",
            "muted": "#475569",
            "border": "#E2E8F0",
            "primary": "#2563EB",      # Blue
            "accent": "#10B981",       # Green
            "button_text": "#FFFFFF",
            "selection": "#DBEAFE",
            "selection_text": "#0F172A",
            "error": "#EF4444",
            "error_bg": "#FEE2E2",
            "warning": "#F59E0B",
            "success": "#10B981",
        }

        dark = {
            "bg": "#121212",
            "surface": "#1E1E1E",
            "surface2": "#2A2A2A",
            "text": "#E5E7EB",
            "muted": "#A1A1AA",
            "border": "#2F2F2F",
            "primary": "#8B5CF6",      # Violet
            "accent": "#22D3EE",       # Cyan
            "button_text": "#0D0D0D",
            "selection": "#374151",
            "selection_text": "#E5E7EB",
            "error": "#EF4444",
            "error_bg": "#7F1D1D",
            "warning": "#F59E0B",
            "success": "#10B981",
        }

        nord = {
            "bg": "#2E3440",
            "surface": "#3B4252",
            "surface2": "#434C5E",
            "text": "#ECEFF4",
            "muted": "#D8DEE9",
            "border": "#4C566A",
            "primary": "#5E81AC",
            "accent": "#88C0D0",
            "button_text": "#ECEFF4",
            "selection": "#5E81AC",
            "selection_text": "#ECEFF4",
            "error": "#BF616A",
            "error_bg": "#3B4252",
            "warning": "#EBCB8B",
            "success": "#A3BE8C",
        }

        dracula = {
            "bg": "#282A36",
            "surface": "#303446",
            "surface2": "#3A3F58",
            "text": "#F8F8F2",
            "muted": "#E2E2DC",
            "border": "#44475A",
            "primary": "#BD93F9",      # Purple
            "accent": "#FF79C6",       # Pink
            "button_text": "#F8F8F2",
            "selection": "#44475A",
            "selection_text": "#F8F8F2",
            "error": "#FF5555",
            "error_bg": "#3A3F58",
            "warning": "#FFB86C",
            "success": "#50FA7B",
        }

        cls._THEMES["Light"] = lambda: build_theme_qss(light)
        cls._THEMES["Dark"] = lambda: build_theme_qss(dark)
        cls._THEMES["Nord"] = lambda: build_theme_qss(nord)
        cls._THEMES["Dracula"] = lambda: build_theme_qss(dracula)
        
        # Store palettes for programmatic access
        cls._PALETTES["Light"] = light
        cls._PALETTES["Dark"] = dark
        cls._PALETTES["Nord"] = nord
        cls._PALETTES["Dracula"] = dracula

    @classmethod
    def list_themes(cls) -> Tuple[str, ...]:
        cls._init_registry()
        return ("System (Auto)",) + tuple(cls._THEMES.keys())

    @classmethod
    def _settings(cls) -> QSettings:
        return QSettings("TaskTitan", "TaskTitan")

    @classmethod
    def get_saved_selection(cls) -> Tuple[str, bool]:
        s = cls._settings()
        theme = s.value("theme/name", "Light")
        follow = s.value("theme/follow_system", True, type=bool)
        return theme, follow

    @classmethod
    def save_selection(cls, theme_name: str, follow_system: bool) -> None:
        s = cls._settings()
        s.setValue("theme/name", theme_name)
        s.setValue("theme/follow_system", follow_system)
        s.sync()

    @classmethod
    def apply_saved_theme(cls, app: QApplication) -> None:
        theme_name, follow = cls.get_saved_selection()
        cls.apply_theme(app, theme_name, follow)

    @classmethod
    def apply_theme(cls, app: QApplication, theme_name: str, follow_system: bool = False) -> None:
        cls._init_registry()

        if follow_system or theme_name == "System (Auto)":
            use_dark = bool(darkdetect.isDark())
            chosen = "Dark" if use_dark else "Light"
        else:
            chosen = theme_name

        loader = cls._THEMES.get(chosen)
        qss = loader() if loader else ""
        # Always reapply full stylesheet to ensure switching works even if the same theme is chosen twice
        app.setStyleSheet("")
        try:
            app.setStyleSheet(qss)
        except Exception:
            app.setStyleSheet("")

        try:
            cls._normalize_and_repolish(app)
        except Exception:
            pass

    @classmethod
    def toggle_dark_light(cls, app: QApplication) -> None:
        current, follow = cls.get_saved_selection()
        if follow:
            current = "Dark" if bool(darkdetect.isDark()) else "Light"
        new_theme = "Dark" if current != "Dark" else "Light"
        cls.save_selection(new_theme, False)
        cls.apply_theme(app, new_theme, False)

    @classmethod
    def get_current_theme_name(cls, follow_system: bool = None) -> str:
        """Get the current active theme name."""
        cls._init_registry()
        if follow_system is None:
            _, follow_system = cls.get_saved_selection()
        
        if follow_system:
            use_dark = bool(darkdetect.isDark())
            return "Dark" if use_dark else "Light"
        
        theme_name, _ = cls.get_saved_selection()
        if theme_name == "System (Auto)":
            use_dark = bool(darkdetect.isDark())
            return "Dark" if use_dark else "Light"
        return theme_name
    
    @classmethod
    def get_current_palette(cls, follow_system: bool = None) -> Dict[str, str]:
        """Get the current theme palette as a dictionary."""
        cls._init_registry()
        theme_name = cls.get_current_theme_name(follow_system)
        return cls._PALETTES.get(theme_name, cls._PALETTES["Light"]).copy()
    
    @classmethod
    def get_color(cls, color_key: str, follow_system: bool = None) -> str:
        """Get a specific color from the current theme palette.
        
        Args:
            color_key: One of 'bg', 'surface', 'surface2', 'text', 'muted', 
                      'border', 'primary', 'accent', 'button_text', 
                      'selection', 'selection_text'
            follow_system: Whether to follow system theme (None uses saved setting)
        
        Returns:
            Hex color string (e.g., "#FFFFFF")
        """
        palette = cls.get_current_palette(follow_system)
        return _hex(palette.get(color_key, palette.get("text", "#000000")))
    
    @classmethod
    def _normalize_and_repolish(cls, app: QApplication) -> None:
        from PyQt6.QtWidgets import QWidget

        clear_object_names = {
            "sidebar",
            "calendar-card",
            "pomodoroHeader",
            "pomodoroSeparator",
            "event-card",
            "detailsItem",
            "dashboardPage",
            "contentStack",
        }

        for w in app.allWidgets():
            try:
                if not isinstance(w, QWidget):
                    continue
                obj = w.objectName() or ""
                ss = w.styleSheet() if hasattr(w, "styleSheet") else ""
                if not ss:
                    continue
                if (obj in clear_object_names) or ("background" in ss or "color:" in ss or "qlineargradient" in ss or "border:" in ss):
                    w.setStyleSheet("")
            except Exception:
                continue

        for w in app.allWidgets():
            try:
                w.style().unpolish(w)
                w.style().polish(w)
                w.update()
            except Exception:
                continue

