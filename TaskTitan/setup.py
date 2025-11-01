"""
Setup script for TaskTitan.

This script handles package installation and distribution.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read version from constants
version = "1.0.0"
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "TaskTitan"))
    from app.resources.constants import APP_VERSION
    version = APP_VERSION
except ImportError:
    pass

setup(
    name="tasktitan",
    version=version,
    description="A comprehensive productivity and task management application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mahan Dashti Gohari",
    author_email="mahan.dashiti.gohari@gmail.com",
    url="https://github.com/mahan2079/TaskTitan",
    packages=find_packages(where="TaskTitan"),
    package_dir={"": "TaskTitan"},
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.5.2",
        "matplotlib>=3.7.2",
        "darkdetect>=0.8.0",
        "qasync>=0.24.0",
        "pyqtgraph>=0.13.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
        "build": [
            "pyinstaller>=5.13.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    entry_points={
        "console_scripts": [
            "tasktitan=app.main:main",
        ],
    },
    package_data={
        "app": [
            "resources/icons/*.svg",
            "themes/*.qss",
        ],
    },
)

