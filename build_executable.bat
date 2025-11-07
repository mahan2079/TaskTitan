@echo off
REM Build script for creating TaskTitan portable Windows executable
REM This script creates a single-file .exe that can run on any Windows system

echo ========================================
echo TaskTitan Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again
    pause
    exit /b 1
)

echo Checking Python version...
python --version
echo.

REM Change to TaskTitan directory
cd /d "%~dp0TaskTitan"
if errorlevel 1 (
    echo ERROR: Cannot find TaskTitan directory
    pause
    exit /b 1
)

echo Installing/updating dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Building executable...
echo This may take several minutes...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the executable
python -m PyInstaller tasktitan.spec --clean --noconfirm

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Copy executable to Executable folder
echo.
echo Copying executable to Executable folder...
cd /d "%~dp0"

if not exist "Executable" mkdir "Executable"

if exist "TaskTitan\dist\TaskTitan.exe" (
    copy /Y "TaskTitan\dist\TaskTitan.exe" "Executable\TaskTitan.exe"
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo Executable location: Executable\TaskTitan.exe
    echo.
    echo The executable is portable and can be run on any Windows system
    echo without requiring Python or any dependencies to be installed.
    echo.
) else (
    echo ERROR: Executable not found in dist folder
    pause
    exit /b 1
)

pause

