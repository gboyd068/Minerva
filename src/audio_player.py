import glob
import os
import json
import threading
import time
from just_playback import Playback
from kivymd.app import MDApp
from kivy.clock import Clock

class AudioPlayer():
    def __init__(self, audio_path=None):
        self.audio_path = audio_path
        self.audio_filenames = None
        self.timestamp_path = None
        self.current_audio_idx = None
        self.playback = None
        self.current_audio_position = None
        self.disable_saving = False
        self.playing = False
        self.audio_thread = None
        self.slider = None
        self.sync_script = None
        # self.slider.value = self.current_audio_position / self.playback.duration
        Clock.schedule_once(self._finish_init)
    
    def _finish_init(self, dt):
        # get a reference for the slider so sync script can update it
        app = MDApp.get_running_app()
        self.slider = app.root.ids.player_screen.ids.audio_slider # kind of hacky
        self.slider.bind(value=self.on_slider_value_change)
        self.sync_script = app.root.ids.player_screen.sync_script

    def load_audio_path(self, audio_path):
        self.audio_filenames = glob.glob(os.path.join(audio_path, "*.mp3"))
        self.timestamp_path = os.path.join(audio_path, "last_played_timestamp.json")

    def load_audio_file(self, audio_file_idx):
        self.current_audio_idx = audio_file_idx
        self.playback = Playback(self.audio_filenames[self.current_audio_idx])
        self.playback.play()
        self.playback.pause()

    def go_to_audio_file_position(self, audio_file_idx, audio_position):
        if  0 <= audio_file_idx < len(self.audio_filenames):
            if audio_file_idx != self.current_audio_idx:
                self.current_audio_idx = audio_file_idx
                self.load_audio_file(self.current_audio_idx)
            if 0 <= audio_position < self.playback.duration:
                self.playback.seek(audio_position)
                self.current_audio_position = audio_position
                Clock.schedule_once(self.set_slider_value)

                self.sync_script.sync_to_audio_position()

            if self.playing:
                self.playback.resume()
            
    
    def set_slider_value(self, dt=None):
        self.slider.value = self.current_audio_position / self.playback.duration



    def go_to_next_audio_file(self):
        self.go_to_audio_file_position(self.current_audio_idx + 1, 0)
    
    def go_to_previous_audio_file(self):
        self.go_to_audio_file_position(self.current_audio_idx - 1, 0)

    def toggle_play(self):
        if not self.playing:
            self.playing = True
            # self.play_button.text = "Pause"
            self.audio_thread = threading.Thread(target=self.audio_play_thread)
            self.audio_thread.start()
        else:
            self.playing = False
            self.playback.pause()
            # self.play_button.text = "Resume"

    def subtitle_time_to_seconds(self, time):
        return (time.hour * 3600 + time.minute * 60 +
                time.second) + time.microsecond / 1000000

    # maybe this main loop should instead go in a syncing class
    def audio_play_thread(self):
        self.playback.seek(self.current_audio_position)
        self.playback.resume()

        while self.playback.playing:
            time.sleep(0.1)
            self.current_audio_position = self.playback.curr_pos
            Clock.schedule_once(self.set_slider_value)
            self.save_last_played_timestamp()

    def on_slider_value_change(self, instance, value):
        # Calculate the new audio position based on the slider value
        new_audio_position = value * self.playback.duration
        if abs(new_audio_position - self.current_audio_position) > 1:
            self.go_to_audio_file_position(self.current_audio_idx, new_audio_position)
        

    def save_last_played_timestamp(self):
        if self.disable_saving:
            return
        try:
            timestamp = {"audio_file_idx": self.current_audio_idx,
                         "audio_position": self.playback.curr_pos}
            with open(self.timestamp_path, "w+") as file:
                json.dump(timestamp, file)
        except FileNotFoundError:
            pass

    def load_last_played_timestamp(self):
        try:
            with open(self.timestamp_path, "r") as file:
                timestamp = json.load(file)
                audio_index = timestamp["audio_file_idx"]
                audio_position = timestamp["audio_position"]
                self.go_to_audio_file_position(audio_index, audio_position)
        except FileNotFoundError:
            self.go_to_audio_file_position(0, 0)