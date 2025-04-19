#!/usr/bin/env python
"""
Launcher script for TaskTitan.

This script ensures the correct Python import paths are set up before launching the application.
"""
import sys
import os

# Add the current directory and parent to the Python path for correct imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Now we can import from app
from app.main import main

if __name__ == "__main__":
    sys.exit(main()) 