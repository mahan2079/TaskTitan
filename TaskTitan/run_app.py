#!/usr/bin/env python
"""
Launcher script for TaskTitan.

This script helps run the TaskTitan application by setting up proper Python paths.
"""
import sys
import os

# Get the directory containing this script
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TaskTitan")

# Add it to the Python path
sys.path.insert(0, app_dir)

# Now we can directly run the main module
from app.main import main

if __name__ == "__main__":
    print("Starting TaskTitan...")
    main() 