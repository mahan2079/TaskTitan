#!/usr/bin/env python
"""
TaskTitan - Alternative entry point with version selection
"""

import sys
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TaskTitan application")
    parser.add_argument('--use-legacy', action='store_true', help='Use legacy version of the application')
    args = parser.parse_args()
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    if args.use_legacy:
        # Run the legacy version - import the module and run it
        print("Starting legacy version of TaskTitan...")
        import TaskTitan
        sys.exit(TaskTitan.main())
    else:
        # Run the modern version directly - import the module we need
        print("Starting TaskTitan...")
        import app.main
        sys.exit(app.main.main()) 