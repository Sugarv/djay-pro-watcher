import time
import requests
import os
import threading
import subprocess
import rumps
import keyring
from dotenv import load_dotenv

# Load environment variables from .env file (fallback for dev)
load_dotenv()

# --- CONFIGURATION ---
FILE_PATH = os.path.expanduser("~/Music/djay/djay Media Library.djayMediaLibrary/NowPlaying.txt")

EMOJI_IDLE = "🎧"
EMOJI_ALERT = "🔔"
EMOJI_ERROR = "⚠️"

class DjayProWatcherApp(rumps.App):
    def __init__(self):
        super(DjayProWatcherApp, self).__init__("DjayProWatcher", title=EMOJI_IDLE, quit_button=None)
        self.monitoring = False
        self.played_history = set()
        self.last_mtime = 0
        self.menu_items = {}
        self.pending_suggestions = None

        # Load API Key (either from Keychain or .env fallback)
        self.api_key = keyring.get_password("DjayProWatcher", "lastfm_api_key") or os.getenv("LASTFM_API_KEY")

        # Setup standard buttons
        self.toggle_btn = rumps.MenuItem("Start Monitoring", callback=self.toggle_monitoring)
        self.statusItem = rumps.MenuItem("Now Playing: Not Monitoring")
        self.set_key_btn = rumps.MenuItem("Update API Key", callback=self.prompt_api_key)
        self.about_btn = rumps.MenuItem("About", callback=self.show_about)
        self.quit_btn = rumps.MenuItem("Quit", callback=rumps.quit_application)
        
        self.base_menu = [
            self.toggle_btn,
            rumps.separator,
            self.statusItem,
            rumps.separator
        ]
        
        # Build initial menu
        self.rebuild_menu([])
        
        # Timer runs on main loop, safe to update UI
        self.timer = rumps.Timer(self.timer_tick, 1)

    def show_about(self, sender):
        rumps.alert(title="Djay Pro Watcher", message="A macOS menu bar app that watches Djay Pro and suggests similar songs using LastFM.\nClick on a suggestion to copy it to your clipboard.\n\nGitHub:\nhttps://github.com/Sugarv/djay-pro-watcher")

    def rebuild_menu(self, suggestions):
        self.menu.clear()
        for item in self.base_menu:
            self.menu.add(item)
            
        if not suggestions:
            self.menu.add(rumps.MenuItem("No suggestions found"))
        else:
            for artist, title in suggestions:
                track_text = f"{artist} - {title}"
                def callback(sender, text=track_text):
                    self.copy_to_clipboard(text)
                self.menu.add(rumps.MenuItem(track_text, callback=callback))
                
        self.menu.add(rumps.separator)
        self.menu.add(self.set_key_btn)
        self.menu.add(self.about_btn)
        self.menu.add(self.quit_btn)

    def update_status(self, msg, is_error=False, emoji=None):
        self.statusItem.title = msg
        if emoji:
            self.title = emoji
        elif is_error:
            self.title = EMOJI_ERROR
        elif not is_error and self.title == EMOJI_ERROR:
            self.title = EMOJI_IDLE

    def prompt_api_key(self, sender=None):
        window = rumps.Window(
            title="LastFM API Key Required",
            message="Please enter your LastFM API key.\nYou can get one at https://www.last.fm/api",
            default_text=self.api_key if self.api_key else "",
            cancel=True
        )
        response = window.run()
        if response.clicked: # User clicked OK
            key = response.text.strip()
            if key:
                self.api_key = key
                keyring.set_password("DjayProWatcher", "lastfm_api_key", key)
                rumps.notification(title="DjayProWatcher", subtitle="Configuration Saved", message="API Key has been securely stored in Keychain.")

    @rumps.clicked("Start Monitoring")
    def toggle_monitoring(self, sender):
        if not self.api_key:
            self.prompt_api_key()
            if not self.api_key:
                self.update_status("Error: API Key required", is_error=True)
                return

        if not self.monitoring:
            if not os.path.exists(os.path.dirname(FILE_PATH)):
                self.update_status(f"Error: Path not found {os.path.dirname(FILE_PATH)}", is_error=True)
                return
            
            self.monitoring = True
            self.toggle_btn.title = "Stop Monitoring"
            self.update_status("Monitoring started...", emoji=EMOJI_IDLE)
            
            # Start timer
            self.timer.start()
            
            # initial check
            self.last_mtime = 0
        else:
            self.monitoring = False
            self.toggle_btn.title = "Start Monitoring"
            self.update_status("Monitoring stopped.", emoji=EMOJI_IDLE)
            self.timer.stop()

    def timer_tick(self, sender):
        # 1. Update UI with pending suggestions if any arrived from background thread
        if self.pending_suggestions is not None:
            self.update_suggestions_ui(self.pending_suggestions)
            self.pending_suggestions = None
            
        # 2. Check file modification
        if not self.monitoring:
            return
            
        try:
            mtime = os.path.getmtime(FILE_PATH)
            if mtime > self.last_mtime:
                # Add a tiny delay to ensure file write is completed
                time.sleep(0.2)
                self.last_mtime = mtime
                self.parse_now_playing()
        except OSError:
            pass

    def parse_now_playing(self):
        if not os.path.exists(FILE_PATH):
            return
        
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            metadata = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
                    
            title = metadata.get("Title")
            artist = metadata.get("Artist")
            
            if title and artist:
                current_track_key = f"{artist} - {title}".lower()
                
                if current_track_key not in self.played_history:
                    self.played_history.add(current_track_key)
                    self.update_status(f"Now Playing: {artist} - {title}", emoji=EMOJI_IDLE)
                    self.fetch_similar_tracks(artist, title)

        except Exception as e:
            print(f"Error reading file: {e}")

    def fetch_similar_tracks(self, artist, title):
        def task():
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "track.getSimilar",
                "artist": artist,
                "track": title,
                "api_key": self.api_key,
                "format": "json",
                "limit": 15
            }
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                if "similartracks" in data and "track" in data["similartracks"]:
                    tracks = data["similartracks"]["track"]
                    suggestions = []
                    for t in tracks:
                        name = t['name']
                        art = t['artist']['name']
                        key = f"{art} - {name}".lower()
                        if key not in self.played_history:
                            suggestions.append((art, name))
                    
                    self.pending_suggestions = suggestions
                else:
                    self.pending_suggestions = []
            except Exception as e:
                print(f"Fetch error: {e}")
                self.pending_suggestions = []

        threading.Thread(target=task, daemon=True).start()

    def update_suggestions_ui(self, suggestions):
        self.rebuild_menu(suggestions)
        # Change icon to indicate new suggestions
        self.title = EMOJI_ALERT

    def copy_to_clipboard(self, text):
        try:
            # Using pbcopy on macOS
            process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            print(f"Copied: {text}")
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
            
        # Reset Icon when user interacts (e.g. copies a suggestion)
        self.title = EMOJI_IDLE

if __name__ == "__main__":
    app = DjayProWatcherApp()
    app.run()