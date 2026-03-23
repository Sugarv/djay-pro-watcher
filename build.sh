#!/bin/bash
# Halt on errors
set -e

echo "Building DjayProWatcher (Apple Silicon arm64)..."

# 1. Build the Native M-series Application using PyInstaller
pyinstaller --onefile --windowed --noconsole \
    --name "DjayProWatcher" \
    --osx-bundle-identifier "com.sugarv.djayprowatcher" \
    --target-architecture arm64 \
    main.py

echo "Build complete. Injecting macOS Privacy Permissions into Info.plist..."

# 2. Inject Privacy Strings using plutil
PLIST_PATH="dist/DjayProWatcher.app/Contents/Info.plist"

# Use -replace instead of -insert in case PyInstaller regenerates them differently, to avoid errors
plutil -replace NSRemovableVolumesUsageDescription -string "DjayProWatcher needs access to your Music folder to read the Now Playing text file." "$PLIST_PATH"
plutil -replace NSDocumentsFolderUsageDescription -string "DjayProWatcher needs access to your Documents folder if you move your Now Playing configuration." "$PLIST_PATH"
plutil -replace NSDesktopFolderUsageDescription -string "DjayProWatcher needs access to your Desktop if you move your Now Playing configuration." "$PLIST_PATH"

# LSUIElement set to 1 forces the app to not show up in the dock (Menu Bar only)
plutil -replace LSUIElement -string "1" "$PLIST_PATH"

echo "Permissions injected. Zipping the application..."

# 3. Zip for distribution
cd dist
# Remove existing zip if it exists so we have a clean archive
rm -f DjayProWatcher.zip
zip -qr DjayProWatcher.zip DjayProWatcher.app
rm -rf DjayProWatcher.app DjayProWatcher

echo "============================================================"
echo "✅ Finished! The distributable zip is located at:"
echo "   dist/DjayProWatcher.zip"
echo "============================================================"
