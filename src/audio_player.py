import glob
import os
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
        self.current_audio_idx = 0
        self.playback = None
        self.current_audio_position = None
        self.disable_saving = False
        self.playing = False
        self.audio_thread = None
        self.slider = None
        # self.slider.value = self.current_audio_position / self.playback.duration
        Clock.schedule_once(self._finish_init)
    
    def _finish_init(self, dt):
        # get a reference for the slider so sync script can update it
        app = MDApp.get_running_app()
        self.slider = app.root.ids.player_screen.ids.audio_slider # kind of hacky
        self.slider.bind(value=self.on_slider_value_change)

    def load_audio_path(self, audio_path):
        self.audio_filenames = glob.glob(os.path.join(audio_path, "*.mp3"))
        self.timestamp_path = os.path.join(audio_path, "last_played_timestamp.txt")

    def load_audio_file(self, audio_file_idx):
        self.current_audio_idx = audio_file_idx
        self.playback = Playback(self.audio_filenames[self.current_audio_idx])
        self.playback.play()
        self.playback.pause()

    def go_to_audio_file_position(self, audio_file_idx, audio_position):
        if  0 <= audio_file_idx < len(self.audio_filenames):
            self.current_audio_idx = audio_file_idx
            self.load_audio_file(self.current_audio_idx)
            self.playback.seek(audio_position)
            if self.playing:
                self.playback.resume()
    
    def go_to_next_audio_file(self):
        self.go_to_audio_file_position(self.current_audio_idx + 1, 0)
    
    def go_to_previous_audio_file(self):
        self.go_to_audio_file_position(self.current_audio_idx - 1, 0)

    def toggle_play(self, instance):
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
            curr_pos = self.playback.curr_pos
            self.slider.value = curr_pos / self.playback.duration
            self.save_last_played_timestamp()
            # DO AUDIO TO EBOOK SYNC HERE ?
            # for idx, subtitle in enumerate(self.subtitle_file):
            #     start_time = subtitle.start.to_time()
            #     end_time = subtitle.end.to_time()

            #     start_time_s = self.subtitle_time_to_seconds(start_time)
            #     end_time_s = self.subtitle_time_to_seconds(end_time)

            #     if start_time_s <= curr_pos <= end_time_s:
            #         if self.current_subtitle_idx == idx:
            #             break
            #         if self.current_subtitle_idx != idx:
            #             self.current_subtitle_idx = idx
            #             Clock.schedule_once(
            #                 lambda dt: self.update_cursor())
            #             break

    def on_slider_value_change(self, instance, value):
        # Calculate the new audio position based on the slider value
        new_audio_position = value * self.playback.duration
        if abs(new_audio_position - self.current_audio_position) > 1:
            self.playback.seek(new_audio_position)
        self.current_audio_position = new_audio_position

    def save_last_played_timestamp(self):
        if self.disable_saving:
            return
        try:
            with open(self.timestamp_path, "w") as file:
                file.write(str(self.playback.curr_pos))

        except FileNotFoundError:
            pass

    def load_last_played_timestamp(self):
        try:
            with open(self.timestamp_path, "r") as file:
                self.current_audio_position = float(file.read())
        except Exception as e:
            print(e)
            self.current_audio_position = 0