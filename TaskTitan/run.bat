@echo off
REM Launcher batch file for TaskTitan.
REM This script ensures the correct Python import paths are set up before launching the application.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Try to run the Python script
python run.py

REM If Python command fails, try python3
if errorlevel 1 (
    python3 run.py
)

REM If both fail, show error message
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python or add it to your PATH environment variable.
    echo.
    pause
    exit /b 1
)

REM Keep window open if there was an error (optional - remove if you want it to close automatically)
if errorlevel 1 (
    pause
)

