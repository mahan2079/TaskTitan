# TaskTitan Resources Module

This module contains resources such as icons, styles, colors, and constants used throughout the TaskTitan application.

## Directory Structure

```
resources/
├── __init__.py          # Package initialization
├── README.md            # This documentation file
├── icons.py             # Icon management module
├── styles.py            # Component styles module
├── colors.py            # Color palette module
├── constants.py         # Application constants
├── utils.py             # Utility functions
└── icons/               # Icon files (SVG format)
    ├── dashboard.svg
    ├── tasks.svg
    ├── goals.svg
    └── ...
```

## Usage

### Icons

```python
from app.resources import get_icon, get_pixmap

# Get an icon for use with buttons, actions, etc.
dashboard_icon = get_icon("dashboard")
button.setIcon(dashboard_icon)

# Get a pixmap for use with labels, etc.
dashboard_pixmap = get_pixmap("dashboard", size=(32, 32))
label.setPixmap(dashboard_pixmap)
```

### Styles

```python
from app.resources import get_component_style

# Apply a component style to a widget
frame.setStyleSheet(get_component_style("dashboard_card"))
```

### Colors

```python
from app.resources import ColorPalette

# Create a color palette (optionally with dark mode)
colors = ColorPalette(is_dark_mode=False)

# Use colors in stylesheets
label.setStyleSheet(f"color: {colors.get_hex('primary')};")

# Use color objects directly
painter.setPen(colors.primary)
```

### Constants

```python
from app.resources import APP_NAME, APP_VERSION, DASHBOARD_VIEW, VIEW_NAMES

# Use constants in code
window.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")

# Use view indices
content_stack.setCurrentIndex(DASHBOARD_VIEW)

# Use view names
label.setText(VIEW_NAMES[DASHBOARD_VIEW])
```

### Utilities

```python
from app.resources import apply_theme, is_dark_mode, get_resource_path

# Apply theme based on system settings
apply_theme(app, use_dark_theme=is_dark_mode())

# Get absolute path to a resource
icon_path = get_resource_path("icons/dashboard.svg")
```

## Adding New Resources

### Icons

1. Add the SVG file to the `icons/` directory
2. Use the icon by name (without extension) with `get_icon()` or `get_pixmap()`

### Styles

1. Add new style constants to `styles.py`
2. Update the `get_component_style()` function to include the new style

### Colors

1. Add new color constants to `colors.py`
2. Add new properties to the `ColorPalette` class if needed

### Constants

1. Add new constants to `constants.py`
2. Update `__init__.py` to export the new constants if they should be available at the module level 