import tkinter as tk
from tkinter import ttk
from just_playback import Playback  # Import AudioPlayback from just_playback
import threading
import time
import pysrt


class SubtitlePlayer:
    def __init__(self, root, subtitle_file, audio_file):
        self.root = root
        self.subtitle_file = pysrt.open(subtitle_file)
        self.current_subtitle_idx = None
        self.pause_event = threading.Event()

        self.subtitle_text = tk.StringVar()

        # Create subtitle text widget
        self.subtitle_text_widget = tk.Text(self.root, font=("Helvetica", 12))
        self.subtitle_text_widget.pack(side="top", fill="both", expand=True)

        # Initialize subtitle text
        self.init_subtitle_text()

        # Create play button
        self.play_button = ttk.Button(
            self.root, text="Play", command=self.toggle_play)
        self.play_button.pack(side="bottom")

        # Bind spacebar to play/pause
        self.root.bind("<space>", self.toggle_play)

        # Use AudioPlayback with the audio file
        self.playback = Playback(audio_file)

        self.audio_thread = None
        self.playing = False

        # Initialize the subtitle text widget with all subtitle text
        self.init_subtitle_text()

    def toggle_play(self):
        if not self.playing:
            self.playing = True
            self.play_button.config(text="Pause")
            self.audio_thread = threading.Thread(target=self.audio_play_thread)
            self.audio_thread.start()
        else:
            self.playing = False
            self.playback.pause()
            self.play_button.config(text="Resume")

    def audio_play_thread(self):
        if not self.playback.active:
            self.playback.play()
        else:
            self.playback.resume()

        # Get current subtitle information

        while self.playback.playing:
            curr_pos = self.playback.curr_pos
            # use the current time to get the current subtitle
            for idx, subtitle in enumerate(self.subtitle_file):
                start_time = subtitle.start.to_time()
                end_time = subtitle.end.to_time()

                # Convert start_time and end_time to milliseconds
                start_ms = (start_time.hour * 3600 + start_time.minute * 60 +
                            start_time.second) * 1000 + start_time.microsecond / 1000
                end_ms = (end_time.hour * 3600 + end_time.minute * 60 +
                          end_time.second) * 1000 + end_time.microsecond / 1000

                if start_ms <= curr_pos * 1000 <= end_ms:
                    if self.current_subtitle_idx == idx:
                        break
                    if self.current_subtitle_idx != idx:
                        self.current_subtitle_idx = idx
                        self.update_subtitle_text()
                        break

    def init_subtitle_text(self):
        # Clear the Text widget and enable it for editing
        self.subtitle_text_widget.config(state=tk.NORMAL)
        self.subtitle_text_widget.delete(1.0, tk.END)

        # Insert all subtitle texts
        subtitles = self.subtitle_file
        all_subtitle_text = "\n".join(
            [subtitle.text.replace('\n', ' ') for subtitle in subtitles])
        self.subtitle_text_widget.insert(tk.END, all_subtitle_text)

        # Disable the Text widget for editing
        self.subtitle_text_widget.config(state=tk.DISABLED)

    def update_subtitle_text(self):
        # remove previous highlight if it exists
        self.subtitle_text_widget.tag_remove("highlight", "1.0", "end")

        # Highlight the current subtitle
        start_index = f"{self.current_subtitle_idx + 1}.0"
        end_index = f"{self.current_subtitle_idx + 1}.end"
        self.subtitle_text_widget.tag_add("highlight", start_index, end_index)
        self.subtitle_text_widget.tag_configure(
            "highlight", background="yellow")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Subtitle Player")

    subtitle_file = "subtitle.srt"
    audio_file = "audio.mp3"

    player = SubtitlePlayer(root, subtitle_file, audio_file)
    root.mainloop()
