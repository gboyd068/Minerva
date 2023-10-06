import threading
import pysrt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from just_playback import Playback


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
        self.play_button = Button(text="Play", on_press=self.toggle_play)
        self.root_layout = BoxLayout(orientation="vertical")
        self.root_layout.add_widget(self.subtitle_text)
        self.root_layout.add_widget(self.play_button)
        self.initialize_text()
        self.load_last_played_timestamp()
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

    def audio_play_thread(self):
        self.playback.seek(self.current_audio_position)
        self.playback.resume()

        while self.playback.playing:
            curr_pos = self.playback.curr_pos
            self.save_last_played_timestamp()
            for idx, subtitle in enumerate(self.subtitle_file):
                start_time = subtitle.start.to_time()
                end_time = subtitle.end.to_time()

                start_ms = (start_time.hour * 3600 + start_time.minute * 60 +
                            start_time.second) * 1000 + start_time.microsecond / 1000
                end_ms = (end_time.hour * 3600 + end_time.minute * 60 +
                          end_time.second) * 1000 + end_time.microsecond / 1000

                if start_ms <= curr_pos * 1000 <= end_ms:
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

    def update_cursor(self):
        self.subtitle_text.cursor = (0, self.current_subtitle_idx)

    def save_last_played_timestamp(self):
        try:
            with open("last_played_timestamp.txt", "w") as file:
                file.write(str(self.playback.curr_pos))
        except FileNotFoundError:
            pass

    def load_last_played_timestamp(self):
        try:
            with open("last_played_timestamp.txt", "r") as file:
                self.current_audio_position = float(file.read())
        except:
            self.current_audio_position = 0


if __name__ == "__main__":
    subtitle_file = "subtitle.srt"
    audio_file = "audio.mp3"
    player = SubtitlePlayerApp(subtitle_file, audio_file)
    player.run()
