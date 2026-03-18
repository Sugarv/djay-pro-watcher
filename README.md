# djay Pro Watcher

djay Pro has brought streaming from Spotify back in version 5.1.10, but it does not suggest similar tracks. 
This Python application monitors **djay Pro's** "Now Playing" track and suggests similar songs using the **Last.fm API**. It currently works only on MacOS.

## Features
- **Real-time Monitoring**: Automatically detects track changes in djay Pro.
- **Similar Tracks**: Fetched from Last.fm to help you find your next mix.
- **Copy to Clipboard**: Quick access to song names via the `📋` icon.
- **Dark Mode UI**: Minimalist Tkinter interface.

## Prerequisites
- **Last.fm API Key**: [Get one here](https://www.last.fm/api/account/create).
- **djay Pro**: Ensure it is configured to share play state (creates `NowPlaying.txt`).

## Setup
1. **Clone** the repository.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create a `.env` file from `.env-example` and add your API key:
   ```env
   LASTFM_API_KEY=your_lastfm_key_here
   ```
4. **Run**:
   ```bash
   python main.py
   ```

## Configuration
The app looks for the djay library file at:
`~/Music/djay/djay Media Library.djayMediaLibrary/NowPlaying.txt`
