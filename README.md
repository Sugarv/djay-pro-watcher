# djay Pro Watcher

[djay Pro](https://www.algoriddim.com/apps) has brought streaming from Spotify back in [version 5.4.3](https://www.algoriddim.com/djay-pro-mac/releasenotes), but it currently does not suggest similar tracks ("Match" feature). 
This Python application monitors **djay Pro's** "Now Playing" track and suggests similar songs using the **Last.fm API**. It works only on MacOS. 

The dist/ folder contains the compiled application only for Apple Silicon (M1/M2/M3/M4) (See [BUILD.md](BUILD.md) for more information).

## Features
- **Real-time Monitoring**: Automatically detects track changes in djay Pro.
- **Similar Tracks**: Fetched from Last.fm to help you find your next mix.
- **Copy to Clipboard**: Click any suggested song in the menu to copy it to your clipboard.
- **macOS Menu Bar UI**: A native, unobtrusive app that lives in your status bar.

## Prerequisites
- **Last.fm API Key**: [Get one here](https://www.last.fm/api/account/create).
- **djay Pro**: Ensure it is configured to share play state (creates `NowPlaying.txt`).

## How to Use

1. **Download and Extract:** Download the latest `DjayProWatcher.zip` release and double-click it to extract the `DjayProWatcher.app`.
2. **Open the App:** Right-click on `DjayProWatcher.app` and choose **Open**. (You must right-click and choose Open the very first time to bypass macOS developer warnings).
3. **Enter API Key:** The first time you run the app, a window will pop up asking for your [Last.fm API Key](https://www.last.fm/api/account/create). Paste your key and click OK.
4. **Start Monitoring:** A DJ icon will appear in your Mac's menu bar (top right, near the clock). Click it and select **Start Monitoring**.
5. **Copy Songs:** As djay Pro plays, similar song suggestions will appear in that menu (a bell icon!). Just click on any song to instantly copy it to your clipboard!

*(If you are a developer and want to run the app from the source code or build for x86, please see [BUILD.md](BUILD.md) for environment setup).*

## Configuration
The app monitors the djay library file at:
`~/Music/djay/djay Media Library.djayMediaLibrary/NowPlaying.txt`
