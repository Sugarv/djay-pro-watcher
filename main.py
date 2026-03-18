import time
import requests
import os
import threading
import tkinter as tk
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
FILE_PATH = os.path.expanduser("~/Music/djay/djay Media Library.djayMediaLibrary/NowPlaying.txt")
WATCH_DIR = os.path.dirname(FILE_PATH)

class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        bg_color = kwargs.pop("bg", "#1e1e1e")
        super().__init__(container, *args, **kwargs)
        self.configure(bg=bg_color)
        
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta)), "units")

class DjayProWatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("djay Pro Watcher")
        self.root.geometry("320x600")
        self.root.configure(bg="#1e1e1e")
        
        # UI Styles
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        self.monitoring = False
        self.played_history = set()
        self.observer = None

        self.setup_ui()

    def setup_ui(self):
        # Header / Control
        self.control_frame = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=10)
        self.control_frame.pack(fill="x")

        self.toggle_btn = tk.Label(
            self.control_frame, 
            text="START MONITORING", 
            bg="#333333", 
            fg="white", 
            padx=10,
            pady=10,
            cursor="hand2",
            font=("Helvetica", 10, "bold"),
            relief="flat"
        )
        self.toggle_btn.bind("<Button-1>", lambda e: self.toggle_monitoring())
        self.toggle_btn.bind("<Enter>", lambda e: self._on_btn_enter())
        self.toggle_btn.bind("<Leave>", lambda e: self._on_btn_leave())
        self.toggle_btn.pack(fill="x")

        # Now Playing Section
        self.now_playing_frame = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=5)
        self.now_playing_frame.pack(fill="x")

        self.now_playing_label = tk.Label(
            self.now_playing_frame, 
            text="NOT MONITORING", 
            fg="#888888", 
            bg="#1e1e1e",
            font=("Helvetica", 9, "italic"),
            wraplength=280
        )
        self.now_playing_label.pack(anchor="w")

        self.current_song_label = tk.Label(
            self.now_playing_frame, 
            text="", 
            fg="#ffffff", 
            bg="#1e1e1e",
            font=("Helvetica", 11, "bold"),
            wraplength=280,
            justify="left"
        )
        self.current_song_label.pack(anchor="w")

        # Suggestions Section
        self.suggestions_frame = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=5)
        self.suggestions_frame.pack(fill="both", expand=True)

        tk.Label(
            self.suggestions_frame, 
            text="RELATED TRACKS:", 
            fg="#aaaaaa", 
            bg="#1e1e1e",
            font=("Helvetica", 8, "bold")
        ).pack(anchor="w", pady=(5, 5))

        self.suggestions_list_container = ScrollableFrame(self.suggestions_frame, bg="#121212")
        self.suggestions_list_container.pack(fill="both", expand=True)
        self.suggestions_list = self.suggestions_list_container.scrollable_frame

    def _on_btn_enter(self):
        color = "#cc4444" if self.monitoring else "#444444"
        self.toggle_btn.config(bg=color)

    def _on_btn_leave(self):
        color = "#cc3333" if self.monitoring else "#333333"
        self.toggle_btn.config(bg=color)

    def toggle_monitoring(self):
        if not self.monitoring:
            if not os.path.exists(WATCH_DIR):
                self.update_status(f"Error: Path not found\n{WATCH_DIR}", is_error=True)
                return
            
            self.monitoring = True
            self.toggle_btn.config(text="STOP MONITORING", bg="#cc3333")
            self.update_status("Monitoring started...")
            
            self.start_observer()
        else:
            self.monitoring = False
            self.toggle_btn.config(text="START MONITORING", bg="#333333")
            self.update_status("Monitoring stopped.")
            self.stop_observer()

    def update_status(self, msg, is_error=False):
        color = "#ff5555" if is_error else "#888888"
        self.now_playing_label.config(text=msg, fg=color)

    def start_observer(self):
        self.event_handler = WatcherHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, WATCH_DIR, recursive=False)
        self.observer.start()
        # Initial check
        self.parse_now_playing()

    def stop_observer(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

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
                    self.root.after(0, self.update_now_playing_ui, artist, title)
                    self.fetch_similar_tracks(artist, title)

        except Exception as e:
            print(f"Error reading file: {e}")

    def update_now_playing_ui(self, artist, title):
        self.now_playing_label.config(text="NOW PLAYING:", fg="#00ccff")
        self.current_song_label.config(text=f"{artist}\n{title}")

    def fetch_similar_tracks(self, artist, title):
        def task():
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "track.getSimilar",
                "artist": artist,
                "track": title,
                "api_key": LASTFM_API_KEY,
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
                    
                    self.root.after(0, self.update_suggestions_ui, suggestions)
                else:
                    self.root.after(0, self.update_suggestions_ui, [])
            except Exception as e:
                print(f"Fetch error: {e}")
                self.root.after(0, self.update_suggestions_ui, [])

        threading.Thread(target=task, daemon=True).start()

    def update_suggestions_ui(self, suggestions):
        # Clear current list
        for widget in self.suggestions_list.winfo_children():
            widget.destroy()

        if not suggestions:
            tk.Label(
                self.suggestions_list, 
                text="No suggestions found.", 
                fg="#666666", 
                bg="#121212",
                font=("Helvetica", 9)
            ).pack(anchor="w", padx=5, pady=5)
            return

        for artist, title in suggestions:
            row = tk.Frame(self.suggestions_list, bg="#121212")
            row.pack(fill="x", pady=1)
            
            track_text = f"{artist} - {title}"
            
            lbl = tk.Label(
                row, 
                text=track_text, 
                fg="#dddddd", 
                bg="#121212",
                font=("Helvetica", 9),
                wraplength=230,
                justify="left"
            )
            lbl.pack(side="left", padx=5, pady=2, anchor="w")
            
            copy_btn = tk.Label(
                row, 
                text="📋", 
                fg="#888888", 
                bg="#121212",
                cursor="hand2",
                font=("Helvetica", 10)
            )
            copy_btn.pack(side="right", padx=5)
            copy_btn.bind("<Button-1>", lambda e, t=track_text: self.copy_to_clipboard(t))
            copy_btn.bind("<Enter>", lambda e, b=copy_btn: b.config(fg="#ffffff"))
            copy_btn.bind("<Leave>", lambda e, b=copy_btn: b.config(fg="#888888"))

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        # Optional: brief visual feedback
        print(f"Copied: {text}")

class WatcherHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_modified(self, event):
        if event.src_path == FILE_PATH:
            time.sleep(0.6)
            self.app.parse_now_playing()

if __name__ == "__main__":
    root = tk.Tk()
    app = DjayProWatcherApp(root)
    
    def on_closing():
        app.stop_observer()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()