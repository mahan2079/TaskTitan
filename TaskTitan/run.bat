@echo off
REM Launcher batch file for TaskTitan.
REM This script ensures the correct Python import paths are set up before launching the application.

REM If run.vbs exists, use it instead (completely silent, no console window)
if exist "%~dp0run.vbs" (
    wscript "%~dp0run.vbs"
    exit /b
)

REM Change to the directory where this batch file is located
cd /d "%~dp0" >nul 2>&1

REM Try to run the Python script silently (using pythonw.exe - no console window)
start /B "" pythonw run.py >nul 2>&1
if errorlevel 1 (
    start /B "" pythonw3 run.py >nul 2>&1
    if errorlevel 1 (
        start /B "" python run.py >nul 2>&1
        if errorlevel 1 (
            start /B "" python3 run.py >nul 2>&1
        )
    )
)

