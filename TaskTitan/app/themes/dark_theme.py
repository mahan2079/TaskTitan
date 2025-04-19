def get_dark_stylesheet():
    """
    Returns a sophisticated, modern, and user-friendly dark theme with elegant purple and warm orange accents.
    Enhances UI interactions with refined color choices for a vibrant and visually appealing interface.
    """
    return """
    /* General Window and Dialog Background */
    QMainWindow, QDialog {
        background-color: #121212;  /* Deep charcoal for a sleek backdrop */
        color: #E0E0E0;             /* Soft white for high readability */
        font-family: 'Segoe UI', sans-serif;  /* Modern and clean font */
        font-size: 14px;
    }

    /* All Widgets */
    QWidget {
        background-color: #1E1E1E;  /* Slightly lighter than main window for contrast */
        color: #E0E0E0;
        border: none;
        padding: 0px;
        margin: 0px;
    }

    /* Input Fields */
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox {
        background-color: #2C2C2C;  /* Dark grey for input backgrounds */
        color: #FFFFFF;
        padding: 8px;
        border-radius: 6px;
        border: 1px solid #555555;
    }
    QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover, QTimeEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
        background-color: #383838;  /* Slightly lighter on hover */
        border-color: #BB86FC;      /* Elegant purple accent on hover */
    }

    /* Tables and Tree Widgets */
    QTreeWidget, QTableWidget, QTreeView {
        background-color: #252525;  /* Darker background for table elements */
        color: #E0E0E0;
        alternate-background-color: #303030;  /* Alternating row colors for readability */
        border-radius: 8px;
        padding: 4px;
    }
    QHeaderView::section {
        background-color: #3C3C3C;  /* Header background with purple tint */
        color: #FFFFFF;
        padding: 8px;
        border: none;
        font-weight: bold;
    }

    /* Buttons */
    QPushButton {
        background-color: #BB86FC;  /* Elegant purple */
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease, transform 0.2s ease;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #9A67EA;  /* Slightly darker purple on hover */
        transform: scale(1.05);     /* Subtle grow effect */
    }
    QPushButton:pressed {
        background-color: #7B4AED;  /* Even darker purple when pressed */
    }

    /* Labels */
    QLabel {
        color: #E0E0E0;
        font-weight: 500;
    }

    /* Tabs */
    QTabWidget::pane {
        background-color: #1E1E1E;
        border: none;
    }
    QTabBar::tab {
        background-color: #2C2C2C;
        color: #E0E0E0;
        padding: 10px 20px;
        border-radius: 6px;
        margin: 2px;
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    QTabBar::tab:selected {
        background-color: #BB86FC;  /* Purple highlight for selected tab */
        color: #000000;
    }
    QTabBar::tab:hover {
        background-color: #3C3C3C;
    }

    /* Menu Bar */
    QMenuBar {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border: none;
    }
    QMenuBar::item:selected {
        background-color: #3C3C3C;
    }
    QMenu {
        background-color: #2C2C2C;
        color: #E0E0E0;
        border-radius: 6px;
    }
    QMenu::item:selected {
        background-color: #BB86FC;
        color: #000000;
    }

    /* Progress Bar */
    QProgressBar {
        background-color: #2C2C2C;
        color: #BB86FC;
        border: none;
        border-radius: 6px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #BB86FC;  /* Purple chunks */
        border-radius: 6px;
    }

    /* Checkboxes */
    QCheckBox {
        color: #E0E0E0;
    }

    /* Scroll Areas */
    QScrollArea {
        background-color: #1E1E1E;
        border: none;
    }

    /* List Widgets and Scroll Bars */
    QListWidget, QScrollBar {
        background-color: #2C2C2C;
        color: #E0E0E0;
        border-radius: 6px;
    }
    QScrollBar:horizontal, QScrollBar:vertical {
        background-color: #1E1E1E;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
        background-color: #BB86FC;  /* Purple handles */
        border-radius: 4px;
    }
    QScrollBar::add-line, QScrollBar::sub-line {
        background-color: #BB86FC;
        border-radius: 4px;
    }
    QScrollBar::add-page, QScrollBar::sub-page {
        background-color: #1E1E1E;
    }

    /* Calendar Widget */
    QCalendarWidget {
        background-color: #1E1E1E; /* Deep dark background for the calendar */
        color: #000000;           /* Default text color for calendar elements set to black */
        border: none;
        font-size: 14px;
    }
    QCalendarWidget QAbstractItemView {
        background-color: #2C2C2C;               /* Slightly lighter background for dates */
        selection-background-color: #FF7043;    /* Vibrant orange for selected dates */
        color: #000000;                         /* Black text for default and selected dates */
        selection-color: #000000;               /* Ensure selected date text is also black */
        gridline-color: #FFA726;                /* Subtle orange for gridlines */
    }
    QCalendarWidget QAbstractItemView::item {
        color: #000000;                         /* Default text color for dates */
        padding: 4px;                           /* Add spacing for readability */
    }

    /* Weekday Column Backgrounds (Monday to Sunday) */
    QCalendarWidget QTableView {
        alternate-background-color: #2E2E2E;   /* Alternating row colors */
        gridline-color: #FFA726;                /* Subtle orange for gridlines */
    }
    QCalendarWidget QTableView::item:enabled {
        background-color: #E0F7FA;             /* Light bluish background for enabled weekdays */
        color: #000000;                        /* Black text for visibility */
    }
    QCalendarWidget QTableView::item:enabled:alternate {
        background-color: #B2EBF2;             /* Slightly darker bluish background for alternating rows */
    }

    /* Navigation Buttons */
    QCalendarWidget QToolButton {
        background-color: #FF7043;             /* Warm orange for navigation buttons */
        color: #000000;                        /* Black text for contrast */
        border-radius: 6px;                    /* Rounded buttons for modern design */
        padding: 4px;                          /* Comfortable padding */
        font-weight: bold;                     /* Bold text for visibility */
    }
    QCalendarWidget QToolButton:hover {
        background-color: #FF5722;             /* Darker orange on hover for interactivity */
    }

    /* Spin Box in Calendar */
    QCalendarWidget QSpinBox {
        background-color: #2C2C2C;             /* Dark grey for spin box */
        color: #000000;                        /* Black text for readability */
        border-radius: 6px;                    /* Rounded corners */
        padding: 4px;                          /* Padding for better spacing */
    }

    /* Header (Day Names) */
    QCalendarWidget QHeaderView {
        background-color: #4DD0E1;             /* Bright bluish header background */
        color: #000000;                        /* Black text for contrast */
        border: none;                          /* Clean header look without borders */
    }
    """ 