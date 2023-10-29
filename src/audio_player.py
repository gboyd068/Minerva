import glob
import os
import json
import threading
import time
from src.playback import Playback
from kivymd.app import MDApp
from kivy.clock import Clock
from json import JSONDecodeError
 
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
        self.disable_auto_slider = False
        self.audio_thread = None
        self.slider = None
        self.sync_script = None
        self.playback_speed = float(MDApp.get_running_app().config.get("General", "playback_speed"))
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

    def load_audio_file(self, audio_file_idx, start_time=0):
        print(start_time)
        self.current_audio_idx = audio_file_idx
        self.playback = Playback(filename=self.audio_filenames[self.current_audio_idx], ff_opts={'ss': start_time,'af': f'atempo={self.playback_speed}', 'vn': True})
        if self.playing:
            self.playback.play()
        print(self.playback.get_pts())
        self.current_audio_position = start_time

    def go_to_audio_file_position(self, audio_file_idx, audio_position, sync=True):
        if  0 <= audio_file_idx < len(self.audio_filenames):
            if audio_file_idx != self.current_audio_idx:
                self.current_audio_idx = audio_file_idx
                self.load_audio_file(self.current_audio_idx, audio_position)

        playing = not self.playback.get_pause()
        if playing:
            self.toggle_play()
        
        if 0 <= audio_position < self.playback.duration:
            audio_position = max(0, audio_position)
            # self.playback.seek(audio_position)
            # self.current_audio_position = audio_position
            self.load_audio_file(self.current_audio_idx, audio_position)
            Clock.schedule_once(self.set_slider_value)
        if audio_position > self.playback.duration:
            self.go_to_next_audio_file()
        if audio_position < 0 and self.current_audio_idx > 0:
            self.go_to_previous_audio_file()
        
        if playing:
            self.toggle_play()

        if sync:
            self.sync_script.sync_to_audio_position()
            
    
    def go_to_next_audio_file(self):
        if self.current_audio_idx < len(self.audio_filenames) - 2:
            self.go_to_audio_file_position(self.current_audio_idx + 1, 0)
    
    def go_to_previous_audio_file(self):
        if self.current_audio_idx > 0:
            self.go_to_audio_file_position(self.current_audio_idx - 1, 0)

    def toggle_play(self):
        """this is probably broken and needs to change"""
        if not self.playing:
            self.playing = True
            # self.play_button.text = "Pause"
            self.audio_thread = threading.Thread(target=self.audio_play_thread)
            self.audio_thread.start()
        else:
            self.playing = False
            self.playback.pause()
            # self.play_button.text = "Resume"

    def subtitle_time_to_seconds(self, sub_start):
        return (sub_start.hours * 3600 + sub_start.minutes * 60 +
                sub_start.seconds) + sub_start.milliseconds / 1000

    def audio_play_thread(self):
        # self.playback.seek(self.current_audio_position)
        self.playback.play()

        while not self.playback.get_pause() and not self.disable_auto_slider:
            time.sleep(0.1)
            self.current_audio_position = self.playback.get_pts()
            Clock.schedule_once(self.set_slider_value)
            self.save_last_played_timestamp()

    def set_slider_value(self, dt=None):
        self.slider.value = self.current_audio_position / self.playback.duration

    def on_slider_value_change(self, instance, value):
        self.disable_auto_slider = True
        # Calculate the new audio position based on the slider value
        new_audio_position = value * self.playback.duration
        if abs(new_audio_position - self.current_audio_position) > 1:
            self.go_to_audio_file_position(self.current_audio_idx, new_audio_position)
        self.disable_auto_slider = False
        

    def save_last_played_timestamp(self):
        if self.disable_saving:
            return
        try:
            timestamp = {"audio_file_idx": self.current_audio_idx,
                         "audio_position": self.playback.get_pts()}
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
        except (FileNotFoundError, JSONDecodeError):
            self.go_to_audio_file_position(0, 0)