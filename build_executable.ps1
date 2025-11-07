# Build script for creating TaskTitan portable Windows executable
# This script creates a single-file .exe that can run on any Windows system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TaskTitan Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Checking Python version..." -ForegroundColor Yellow
    Write-Host $pythonVersion
    Write-Host ""
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to TaskTitan directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskTitanPath = Join-Path $scriptPath "TaskTitan"

if (-not (Test-Path $taskTitanPath)) {
    Write-Host "ERROR: Cannot find TaskTitan directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location $taskTitanPath

Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
python -m pip install pyinstaller --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Building executable..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow
Write-Host ""

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Build the executable
python -m PyInstaller tasktitan.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Copy executable to Executable folder
Write-Host ""
Write-Host "Copying executable to Executable folder..." -ForegroundColor Yellow
Set-Location $scriptPath

if (-not (Test-Path "Executable")) {
    New-Item -ItemType Directory -Path "Executable" | Out-Null
}

$exeSource = Join-Path $taskTitanPath "dist\TaskTitan.exe"
$exeDest = Join-Path $scriptPath "Executable\TaskTitan.exe"

if (Test-Path $exeSource) {
    Copy-Item $exeSource $exeDest -Force
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable location: Executable\TaskTitan.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The executable is portable and can be run on any Windows system" -ForegroundColor Green
    Write-Host "without requiring Python or any dependencies to be installed." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "ERROR: Executable not found in dist folder" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

