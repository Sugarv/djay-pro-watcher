# Building DjayProWatcher for Release (macOS)

This guide walks you through the process of compiling your Python application into a standalone macOS `.app` bundle, applying necessary privacy permissions, and distributing it via a `.zip` file.

## Development Setup

If you want to run the app directly from the source code, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sugarv/djaypro_watcher.git
   cd djaypro_watcher
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app:**
   ```bash
   python main.py
   ```

## 1. Install Build Tools

Make sure you have `PyInstaller` installed in your environment:

```bash
pip install pyinstaller
```

## 2. Initial PyInstaller Build

You can compile the app specifically for Intel (`x86_64`), specifically for Apple Silicon (`arm64`), or a Universal App (`universal2`) that runs natively on both.

> [!WARNING]
> ### Building a Universal App
> To successfully build a `universal2` executable, **if using Apple Silicon, you cannot use Homebrew's Python** (which is permanently tied to your host machine's architecture, such as `arm64`). 
> 
> You must do the following instead:
> 1. Download the official "macOS 64-bit universal2 installer" directly from [python.org/downloads/macos/](https://www.python.org/downloads/macos/).
> 2. Create a fresh virtual environment using that exact Python install (e.g., `/usr/local/bin/python3 -m venv universal_env`).
> 3. Activate it and re-install all dependencies (`pip install pyinstaller rumps keyring python-dotenv requests`).
> 4. Run PyInstaller with `--target-architecture universal2`.

**To build a Universal App (Intel & Apple Silicon):**
```bash
pyinstaller --onefile --windowed --noconsole --name "DjayProWatcher" --osx-bundle-identifier "com.sugarv.djayprowatcher" --target-architecture universal2 main.py
```

**To build specifically for Apple Silicon (M1/M2/M3):**
```bash
pyinstaller --onefile --windowed --noconsole --name "DjayProWatcher" --osx-bundle-identifier "com.sugarv.djayprowatcher" --target-architecture arm64 main.py
```

**To build specifically for Intel (x86_64):**
```bash
pyinstaller --onefile --windowed --noconsole --name "DjayProWatcher" --osx-bundle-identifier "com.sugarv.djayprowatcher" --target-architecture x86_64 main.py
```

This generates two folders:
*   `build/` (temp files)
*   `dist/` (contains your final `DjayProWatcher.app`)
*   `DjayProWatcher.spec` (The configuration file for your build)

## 3. Injecting the macOS Privacy Flags (Info.plist)

Because the app reads `~/Music`, macOS requires you to declare why you need file system access inside a file called `Info.plist` (which lives inside the `.app` bundle). 

We have provided an `Info.plist` file in the project. The easiest way to inject these permissions into the PyInstaller app is to use macOS's built-in `plutil` command after the build finishes.

Run this command in your terminal right after PyInstaller finishes:

```bash
plutil -insert NSRemovableVolumesUsageDescription -string "DjayProWatcher needs access to your Music folder to read the Now Playing text file in the djay Media Library." dist/DjayProWatcher.app/Contents/Info.plist
plutil -insert NSDocumentsFolderUsageDescription -string "DjayProWatcher needs access to your Documents folder if you move your Now Playing configuration." dist/DjayProWatcher.app/Contents/Info.plist
plutil -insert NSDesktopFolderUsageDescription -string "DjayProWatcher needs access to your Desktop if you move your Now Playing configuration." dist/DjayProWatcher.app/Contents/Info.plist
plutil -insert LSUIElement -string "1" dist/DjayProWatcher.app/Contents/Info.plist
```

*(This directly edits the built `.app` bundle to include the permission prompts).*

### Note on Gatekeeper Security
Because you are distributing this as a `.zip` file without using an Apple Developer Account to officially sign and notarize it, users will see an *"App cannot be opened because the developer cannot be verified"* warning. 
