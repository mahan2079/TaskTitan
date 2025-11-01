# TaskTitan Portable Executable

This folder contains the portable Windows executable for TaskTitan.

## Building the Executable

To build the portable executable, run one of the following scripts from the project root:

### Windows Batch Script
```batch
build_executable.bat
```

### PowerShell Script
```powershell
.\build_executable.ps1
```

The build process will:
1. Install/update all required dependencies
2. Install PyInstaller
3. Build a single-file portable executable
4. Copy the executable to this folder

## Using the Executable

Once built, `TaskTitan.exe` will be available in this folder. This executable:
- Is completely portable - no installation required
- Works on any Windows system (Windows 7+)
- Does not require Python or any dependencies to be installed
- Can be run from any location (USB drive, network share, etc.)

## Data Storage

The executable will create a `data` folder in the same directory as the executable to store:
- Database files (`tasktitan.db`)
- Configuration files (`config.json`)
- Logs (`logs/tasktitan.log`)
- Backups (`backups/`)
- Attachments (`attachments/`)

## Distribution

You can distribute the executable by:
1. Copying `TaskTitan.exe` to any Windows system
2. Running it directly - no installation required
3. The application will create its data folder automatically on first run

## Troubleshooting

If the executable fails to run:
1. Ensure you're running on Windows 7 or later
2. Check Windows Defender or antivirus - it may flag new executables
3. Try running as administrator if permission issues occur
4. Check the `logs/tasktitan.log` file in the data folder for error details

## File Size

The executable is typically 50-100 MB in size as it includes:
- Python runtime
- PyQt6 libraries
- All dependencies (matplotlib, pyqtgraph, etc.)
- Application code and resources

