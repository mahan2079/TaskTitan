# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TaskTitan.
Creates a portable single-file Windows executable.
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Get the base directory (TaskTitan folder)
base_dir = Path(__file__).parent.resolve()

# Entry point - run.py is in the TaskTitan directory
entry_script = str(base_dir / 'run.py')

# Collect all data files
datas = [
    # Icons
    (str(base_dir / 'app' / 'resources' / 'icons'), 'app/resources/icons'),
    # Themes
    (str(base_dir / 'app' / 'themes' / 'style.qss'), 'app/themes'),
    (str(base_dir / 'app' / 'themes' / '__init__.py'), 'app/themes'),
    (str(base_dir / 'app' / 'themes' / 'dark_theme.py'), 'app/themes'),
]

# Hidden imports for PyQt6 and other modules
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtSql',
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qtagg',
    'darkdetect',
    'qasync',
    'pyqtgraph',
    'sqlite3',
    'bcrypt',
    'cryptography',
    'cryptography.fernet',
]

a = Analysis(
    [entry_script],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests',
        'numpy.tests',
        'pytest',
        'tkinter',
        'pydoc',
        'unittest',
        'email',
        'http',
        'xml',
        'html',
        'pdb',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icon path
icon_path = str(base_dir.parent / 'icon.ico')
if not os.path.exists(icon_path):
    icon_path = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TaskTitan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if icon_path else None,
    version_file=None,
)
