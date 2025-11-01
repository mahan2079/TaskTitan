# TaskTitan Build Scripts

## Building Executables

### Windows

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller tasktitan.spec

# The executable will be in dist/TaskTitan.exe
```

### Linux

```bash
# Install dependencies
pip install pyinstaller

# Build executable
pyinstaller tasktitan.spec

# The executable will be in dist/TaskTitan
```

### macOS

```bash
# Install dependencies
pip install pyinstaller

# Build executable
pyinstaller tasktitan.spec

# The executable will be in dist/TaskTitan.app
```

## Creating Installers

### Windows (NSIS)

1. Install NSIS: https://nsis.sourceforge.io/
2. Create installer script (installer.nsi)
3. Compile: `makensis installer.nsi`

### Linux (AppImage)

```bash
# Use appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage dist/TaskTitan.AppDir TaskTitan-x86_64.AppImage
```

### macOS (DMG)

```bash
# Create DMG using hdiutil
hdiutil create -volname "TaskTitan" -srcfolder dist/TaskTitan.app -ov -format UDZO TaskTitan.dmg
```

## Version Management

Versions are managed in `app/resources/constants.py`:
- Update `APP_VERSION` before building
- Tag releases: `git tag v1.0.0`
- Push tags: `git push --tags`

## Automated Releases

Releases are automated via GitHub Actions:
- Push a tag starting with 'v' to trigger release
- Workflow builds for Windows, macOS, and Linux
- Creates GitHub release with all artifacts

