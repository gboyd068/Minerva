import tkinter as tk
from tkinter import ttk
from pydub import AudioSegment
from pydub.playback import play
import threading
import time
import pysrt
import os
import tempfile

class SubtitlePlayer:
    def __init__(self, root, subtitle_file, audio_file):
        self.root = root
        self.subtitle_file = pysrt.open(subtitle_file)
        self.audio_file = AudioSegment.from_mp3(audio_file)
        self.current_subtitle_idx = 0
        self.current_audio_position = 0  # Initialize the current audio position

        self.subtitle_text = tk.StringVar()

        # Create a scrollable Text widget to display subtitles
        self.subtitle_text_widget = tk.Text(root, wrap=tk.WORD)
        self.subtitle_text_widget.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.subtitle_text_widget.config(state=tk.DISABLED)

        self.play_button = ttk.Button(root, text="Play", command=self.play_audio)
        self.play_button.pack()

        self.audio_thread = None
        self.playing = False
        self.audio_buffer = None

        # Load the last played timestamp if available
        self.load_last_played_timestamp()
        # Initialize the subtitle text widget with all subtitle text
        self.init_subtitle_text()

    def play_audio(self):
        if not self.playing:
            self.playing = True
            self.play_button.config(text="Pause")
            self.audio_thread = threading.Thread(target=self.audio_play_thread)
            self.audio_thread.start()
        else:
            self.playing = False
            self.play_button.config(text="Resume")

    def audio_play_thread(self):
        for idx, subtitle in enumerate(self.subtitle_file):
            if not self.playing:
                break

            # Get current subtitle information
            self.current_subtitle_idx = idx
            self.update_subtitle_text()

            start_time = subtitle.start.to_time()
            end_time = subtitle.end.to_time()

            # Get start and end time of next subtitle
            if idx + 1 < len(self.subtitle_file):
                next_subtitle = self.subtitle_file[idx + 1]
                next_start_time = next_subtitle.start.to_time()
                next_end_time = next_subtitle.end.to_time()
            else:
                next_start_time = None
                next_end_time = None

            # Convert start_time and end_time to milliseconds
            start_ms = (start_time.hour * 3600 + start_time.minute * 60 + start_time.second) * 1000 + start_time.microsecond / 1000
            end_ms = (end_time.hour * 3600 + end_time.minute * 60 + end_time.second) * 1000 + end_time.microsecond / 1000

            # Convert next_start_time and next_end_time to milliseconds
            if next_start_time is not None:
                next_start_ms = (next_start_time.hour * 3600 + next_start_time.minute * 60 + next_start_time.second) * 1000 + next_start_time.microsecond / 1000
                next_end_ms = (next_end_time.hour * 3600 + next_end_time.minute * 60 + next_end_time.second) * 1000 + next_end_time.microsecond / 1000
            else:
                next_start_ms = None
                next_end_ms = None

            # Extract audio segment using the buffer if it is not None  
            if self.audio_buffer is not None:
                audio_segment = self.audio_buffer
            else:
                audio_segment = self.audio_file[start_ms:end_ms]

            # Play the audio segment directly and save the current audio position
            time_before_audio = time.time()
            target_time = time_before_audio + (end_ms - start_ms) / 1000
            play(audio_segment)

            # Load the next segment of audio into the buffer using next_start_ms and next_end_ms
            if next_start_ms is not None:
                self.audio_buffer = self.audio_file[next_start_ms:next_end_ms]
            else:
                self.audio_buffer = None

            # Sleep to keep subtitles and audio synchronized
            current_time = time.time()
            time_to_sleep = target_time - current_time
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)



    def init_subtitle_text(self):
        # Clear the Text widget and enable it for editing
        self.subtitle_text_widget.config(state=tk.NORMAL)
        self.subtitle_text_widget.delete(1.0, tk.END)

        # Insert all subtitle texts
        subtitles = self.subtitle_file
        all_subtitle_text = "\n".join([subtitle.text for subtitle in subtitles])
        self.subtitle_text_widget.insert(tk.END, all_subtitle_text)

        # Disable the Text widget for editing
        self.subtitle_text_widget.config(state=tk.DISABLED)

    def update_subtitle_text(self):
        # Highlight the current subtitle
        start_index = f"{self.current_subtitle_idx + 1}.0"
        end_index = f"{self.current_subtitle_idx + 1}.end"
        self.subtitle_text_widget.tag_add("highlight", start_index, end_index)
        self.subtitle_text_widget.tag_configure("highlight", background="yellow")

    def load_last_played_timestamp(self):
        try:
            # Load the last played timestamp from a file
            with open("last_played_timestamp.txt", "r") as file:
                self.current_audio_position = int(file.read())
        except FileNotFoundError:
            pass

    def save_last_played_timestamp(self):
        # Save the current audio position to a file
        with open("last_played_timestamp.txt", "w") as file:
            file.write(str(self.current_audio_position))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Subtitle Player")

    subtitle_file = "subtitle.srt"
    audio_file = "audio.mp3"

    player = SubtitlePlayer(root, subtitle_file, audio_file)
    root.mainloop()