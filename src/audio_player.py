import glob
import os
import threading
import time
import pysrt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.slider import Slider
from just_playback import Playback

class AudioPlayer():
    def __init__(self, audio_path=None):
        self.audio_path = audio_path
        self.current_audio_idx = 0
        self.playback = None
        self.current_audio_position = None
        self.disable_saving = False
        self.playing = False
        self.audio_thread = None
        
        # THESE NEED TO GO INTO A LOADING FUNCTION
        # load the last played timestamp and load relevant audio file
        # self.audio_filenames = glob.glob(os.path.join(audio_path, "*.mp3"))
        # self.timestamp_path = audio_path
        # self.load_last_played_timestamp()


        # self.slider = Slider(min=0, max=1, value=0, step=0.01)
        # self.slider.bind(value=self.on_slider_value_change)
        # self.play_button = Button(text="Play", on_press=self.toggle_play)
        # initialize player

        
        # self.slider.value = self.current_audio_position / self.playback.duration
        # self.playback.play()
        # self.playback.pause()

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



class SubtitlePlayerApp(App):
    def __init__(self, subtitle_file, audio_file):
        super(SubtitlePlayerApp, self).__init__()
        self.subtitle_file = pysrt.open(subtitle_file)
        self.current_subtitle_idx = None
        self.playback = Playback(audio_file)
        self.playing = False
        self.audio_thread = None
        self.subtitle_text = TextInput(
            font_size=16, readonly=True, multiline=True)
        self.subtitle_text.cursor_blink = True
        self.slider = Slider(min=0, max=1, value=0, step=0.01)
        self.slider.bind(value=self.on_slider_value_change)
        self.play_button = Button(text="Play", on_press=self.toggle_play)
        # make layout
        self.root_layout = BoxLayout(orientation="vertical")
        self.root_layout.add_widget(self.subtitle_text)
        self.root_layout.add_widget(self.play_button)
        self.root_layout.add_widget(self.slider)
        # initialize player
        self.initialize_text()
        self.current_audio_position = None
        self.disable_saving = False
        self.load_last_played_timestamp()
        self.slider.value = self.current_audio_position / self.playback.duration
        self.playback.play()
        self.playback.pause()

    def build(self):
        return self.root_layout

    def toggle_play(self, instance):
        if not self.playing:
            self.playing = True
            self.play_button.text = "Pause"
            self.audio_thread = threading.Thread(target=self.audio_play_thread)
            self.audio_thread.start()
        else:
            self.playing = False
            self.playback.pause()
            self.play_button.text = "Resume"

    def subtitle_time_to_seconds(self, time):
        return (time.hour * 3600 + time.minute * 60 +
                time.second) + time.microsecond / 1000000

    def audio_play_thread(self):
        self.playback.seek(self.current_audio_position)
        self.playback.resume()

        while self.playback.playing:
            time.sleep(0.1)
            curr_pos = self.playback.curr_pos
            self.slider.value = curr_pos / self.playback.duration
            self.save_last_played_timestamp()
            # convert this to binary search
            for idx, subtitle in enumerate(self.subtitle_file):
                start_time = subtitle.start.to_time()
                end_time = subtitle.end.to_time()

                start_time_s = self.subtitle_time_to_seconds(start_time)
                end_time_s = self.subtitle_time_to_seconds(end_time)

                if start_time_s <= curr_pos <= end_time_s:
                    if self.current_subtitle_idx == idx:
                        break
                    if self.current_subtitle_idx != idx:
                        self.current_subtitle_idx = idx
                        Clock.schedule_once(
                            lambda dt: self.update_cursor())
                        break

    def set_subtitle_text(self, text):
        self.subtitle_text.text = text

    def initialize_text(self):
        subtitle_text = "\n".join([subtitle.text.replace(
            '\n', ' ') for subtitle in self.subtitle_file])
        Clock.schedule_once(lambda dt: self.set_subtitle_text(subtitle_text)
                            )

    def on_slider_value_change(self, instance, value):
        # Calculate the new audio position based on the slider value
        new_audio_position = value * self.playback.duration
        if abs(new_audio_position - self.current_audio_position) > 1:
            self.playback.seek(new_audio_position)
        self.current_audio_position = new_audio_position

    def update_cursor(self):
        self.subtitle_text.cursor = (0, self.current_subtitle_idx)

    def save_last_played_timestamp(self):
        if self.disable_saving:
            return
        try:
            with open("last_played_timestamp.txt", "w") as file:
                file.write(str(self.playback.curr_pos))

        except FileNotFoundError:
            pass

    def load_last_played_timestamp(self):
        print("loading last played timestamp")
        try:
            with open("last_played_timestamp.txt", "r") as file:
                self.current_audio_position = float(file.read())
        except Exception as e:
            print(e)
            self.current_audio_position = 0

    def on_stop(self):

        self.save_last_played_timestamp()
        self.disable_saving = True
        if self.playback.playing:
            self.toggle_play(self.play_button)
        self.playback.stop()


if __name__ == "__main__":
    subtitle_file = "alloy/subs/alloy1.srt"
    audio_file = "alloy/audio/alloy1.mp3"
    player = SubtitlePlayerApp(subtitle_file, audio_file)
    player.run()
