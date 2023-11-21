import glob
import os
import pathlib
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
        self.end_audio_thread = False
        self.start_time = 0
        self.slider = None
        self.sync_script = None
        self.eof_reached = False
        self.playback_speed = float(MDApp.get_running_app().config.get("General", "playback_speed"))
        Clock.schedule_once(self._finish_init)
    
    def _finish_init(self, dt):
        # get a reference for the slider so sync script can update it
        app = MDApp.get_running_app()
        self.slider = app.root.player_screen.audio_slider
        self.slider.bind(value=self.on_slider_value_change)
        self.sync_script = app.root.player_screen.sync_script

    def load_audio_path(self, audio_path):
        self.audio_filenames = glob.glob(os.path.join(audio_path, "*.mp3"))
        book_dir_name = str(pathlib.Path(audio_path).parents[0])
        user_data_dir = MDApp.get_running_app().user_data_dir
        self.timestamp_path = os.path.join(user_data_dir, book_dir_name, "last_played_timestamp.json")

    def audio_callback(self, selector,value):
            if selector == "read:exit":
                Clock.schedule_once(self.set_slider_value)
            if selector == "eof":
                print("eof")
                self.playback.pause()
                self.eof_reached = True


    def load_audio_file(self, audio_file_idx, start_time=0):
        # FUCK THIS IS CALLED FROM AUDIO_PLAY_THREAD USUALLY BUT MAY BE CALLED FROM ELSEWHERE!
        print("loading audio file")
        self.start_time  = start_time
        self.current_audio_idx = audio_file_idx
        self.playback = Playback(filename=self.audio_filenames[self.current_audio_idx], callback=self.audio_callback, ff_opts={'af': f'atempo={self.playback_speed}','ss': start_time, 'vn': True})
        # if self.playing:
        #     self.audio_thread = threading.Thread(target=self.audio_play_thread)
        #     self.audio_thread.start()
        self.current_audio_position = start_time

    def go_to_audio_file_position(self, audio_file_idx, audio_position, sync=True):
        if  0 <= audio_file_idx < len(self.audio_filenames):
            if audio_file_idx != self.current_audio_idx:
                self.current_audio_idx = audio_file_idx
                self.load_audio_file(self.current_audio_idx, audio_position)

        # playing = not self.playback.get_pause()
        # if playing:
        #     self.toggle_play()
        if audio_file_idx == self.current_audio_idx:
            if 0 <= audio_position < self.playback.duration:
                audio_position = max(0, audio_position)
                # self.playback.seek(audio_position)
                # self.current_audio_position = audio_position
                self.load_audio_file(self.current_audio_idx, audio_position)
            if audio_position > self.playback.duration:
                self.go_to_next_audio_file()
            if audio_position < 0 and self.current_audio_idx > 0:
                self.go_to_previous_audio_file()
        
        # if playing:
        #     self.toggle_play()

        if sync:
            self.sync_script.sync_to_audio_position()
        self.disable_auto_slider = False
            
    
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

        while not self.playback.get_pause():
            if self.end_audio_thread:
                print("ending thread")
                self.end_audio_thread = False
                break

            
            if self.eof_reached:
                self.eof_reached = False
                self.disable_auto_slider = True
                self.go_to_next_audio_file()
                break # end this thread

            time.sleep(0.1)

            if not self.disable_auto_slider:
                self.current_audio_position = self.playback.get_pts()
                # see if the page should be turned based on the current audio position
                if self.sync_script.auto_page_turn_enabled:
                    file_time = self.sync_script.file_time_from_bookpos(self.sync_script.end_page_bookpos)
                    NEXT_PAGE_LEEWAY = 5 # WARNING HACK
                    time_diff_to_page_turn = file_time[1] + NEXT_PAGE_LEEWAY - self.start_time
                    time_diff_from_start = (self.current_audio_position - self.start_time) * self.playback_speed
                    print(time_diff_to_page_turn, time_diff_from_start)
                    if time_diff_from_start > time_diff_to_page_turn:
                        # need to make sure it only turns the page once!
                        Clock.schedule_once(lambda dt: self.sync_script.reader_window.next_page())
                        time.sleep(1)
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
            if not os.path.exists(os.path.dirname(self.timestamp_path)):
                os.makedirs(os.path.dirname(self.timestamp_path))
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