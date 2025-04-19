#!/usr/bin/env python
"""
Launcher script for TaskTitan.

This script ensures the correct Python import paths are set up before launching the application.
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Now we can import from app
from app.main import main

if __name__ == "__main__":
    main() 