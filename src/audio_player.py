import glob
import os
import pathlib
import json
import threading
import time
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.utils import platform
from json import JSONDecodeError
from oscpy.server import OSCThreadServer
if platform != "android":
    from audioservice import service_thread
 
class AudioPlayer():
    def __init__(self, audio_path=None):
        self.audio_path = audio_path
        self.audio_filenames = None
        self.timestamp_path = None
        self.current_audio_idx = None
        self.current_audio_position = None
        self.disable_saving = False
        self.is_playing = False
        self.is_audio_loaded = False
        self.enable_status_update = False
        self.start_time = 0
        self.duration = None
        self.slider = None
        self.sync_script = None
        # threading logic
        self.audio_thread = None
        # events
        self.eof_reached = threading.Event()
        self.end_audio_thread = threading.Event()
        self.finished_loading_audio = threading.Event()

        self.playback_speed = float(MDApp.get_running_app().config.get("General", "playback_speed"))
        Clock.schedule_once(self._finish_init)

        # OSC
        self.osc = None
        self.app_port = 8000
        self.service_port = 8001
        self.osc = OSCThreadServer()
        self.osc.listen(address='localhost', port=self.app_port, default=True)
        # use osc addresses to determine which function to callback
        self.osc.bind(b'/status', self.status_update)

        # start the service thread, should be a service on android
        if platform != "android":
            threading.Thread(target=service_thread, args=(self.app_port, self.service_port), daemon=True).start()
        if platform == "android":
            from jnius import autoclass
            from jnius import cast
            from android import mActivity
            context =  mActivity.getApplicationContext()
            service_name = str(context.getPackageName()) + '.Service' + "Audioservice"
            print("ATTEMPTING TO START SERVICE: ", service_name)
            service = autoclass(service_name)
            self.mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            argument = ''
            service.start(self.mActivity, argument)
            self.service = service


    def _finish_init(self, dt):
        # get a reference for the slider so sync script can update it
        app = MDApp.get_running_app()
        self.slider = app.root.player_screen.audio_slider
        self.slider.bind(value=self.on_slider_value_change)
        self.sync_script = app.root.player_screen.sync_script
        

    def send_message(self, address, values):
        self.osc.send_message(address, values, 'localhost', self.service_port)

    def update_filenames(self, filenames):
        bfilenames = [str.encode(filename) for filename in filenames]
        self.send_message(b'/update_filenames', bfilenames)

    def status_update(self, *values):
        """
        called when status is updated from the service
        values = (current_audio_idx, current_audio_position: float, is_playing: int, duration: float)
        """
        if self.enable_status_update:
            self.is_playing = bool(values[2])
            if self.is_playing:
                self.current_audio_idx = int(values[0])
                self.current_audio_position = float(values[1])
            self.duration = float(values[3])

            # update slider
            if self.is_playing:
                Clock.schedule_once(self.set_slider_value)

            # update play/pause button

            # turn page if required
            if self.sync_script.auto_page_turn_enabled and self.is_playing:
                file_time = self.sync_script.file_time_from_bookpos(self.sync_script.end_page_bookpos)
                file_index = file_time[0]
                NEXT_PAGE_LEEWAY = 5 # WARNING HACK
                time_diff_to_page_turn = file_time[1] + NEXT_PAGE_LEEWAY - self.start_time
                time_diff_from_start = (self.current_audio_position - self.start_time) * self.playback_speed
                print(time_diff_to_page_turn, time_diff_from_start)
                if time_diff_from_start > time_diff_to_page_turn and file_index == self.current_audio_idx:
                    Clock.schedule_once(lambda dt: self.sync_script.reader_window.next_page())
                    time.sleep(1)
                    # might need to adjust this to make sure page turn only happens once

            # save timestamp
            self.save_last_played_timestamp()


    def load_audio_path(self, audio_path):
        self.audio_filenames = glob.glob(os.path.join(audio_path, "*.mp3"))
        book_dir_name = str(pathlib.Path(audio_path).parents[0])
        user_data_dir = MDApp.get_running_app().user_data_dir
        self.timestamp_path = os.path.join(user_data_dir, book_dir_name,
                                           "last_played_timestamp.json")
        self.update_filenames(self.audio_filenames)


    def load_audio_file(self, audio_file_idx, start_time=0):
        self.current_audio_idx = audio_file_idx
        self.send_message(b'/load_audio_file', [audio_file_idx, start_time, self.is_playing])
        self.current_audio_position = start_time
        self.is_audio_loaded = True

    def seek(self, audio_position):
        """
        audio_position: float
                audio position in seconds
        """
        self.send_message(b'/seek', [audio_position])


    def go_to_audio_file_position(self, audio_file_idx, audio_position, sync=True):
        # should probably test that the audio_position is within the duration
        print("go_to_audio_file_position", audio_file_idx, audio_position)
        print("current_audio_idx", self.current_audio_idx)
        print("current_audio_position", self.current_audio_position)
        if not 0 <= audio_file_idx < len(self.audio_filenames):
            print("audio file index out of range")
            audio_file_idx = 0
            audio_position = 0
        if audio_file_idx != self.current_audio_idx:
            self.current_audio_idx = audio_file_idx
            self.current_audio_position = audio_position
            self.load_audio_file(self.current_audio_idx, audio_position)
        else:
            self.seek(audio_position)

        self.current_audio_idx = audio_file_idx
        self.current_audio_position = audio_position
        if sync:
            self.sync_script.sync_to_audio_position()


    def go_to_next_audio_file(self):
        if self.current_audio_idx < len(self.audio_filenames) - 1:
            self.go_to_audio_file_position(self.current_audio_idx + 1, 0)

    def go_to_previous_audio_file(self):
        if self.current_audio_idx > 0:
            self.go_to_audio_file_position(self.current_audio_idx - 1, 0)

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        self.send_message(b'/play', [])

    def pause(self):
        self.send_message(b'/pause', [])

    
        

    def subtitle_time_to_seconds(self, sub_start):
        return (sub_start.hours * 3600 + sub_start.minutes * 60 +
                sub_start.seconds) + sub_start.milliseconds / 1000


    def set_slider_value(self, dt=None):
        self.slider.value = self.current_audio_position / self.duration



    def on_slider_value_change(self, instance, value):
        pos = self.slider.value
        # Calculate the new audio position based on the slider value
        new_audio_position = pos * self.duration
        if abs(new_audio_position - self.current_audio_position) > 1:
            self.enable_status_update = False
            self.go_to_audio_file_position(self.current_audio_idx, new_audio_position)
            self.enable_status_update = True


    def save_last_played_timestamp(self):
        if self.disable_saving:
            return
        try:
            timestamp = {"audio_file_idx": self.current_audio_idx,
                         "audio_position": self.current_audio_position}
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
            

    def change_playback_speed(self, playback_speed):
        self.playback_speed = playback_speed
        self.send_message(b'/update_settings', [playback_speed])