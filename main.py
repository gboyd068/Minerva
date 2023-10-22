from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

from src.library_screen import LibraryScreen
from src.player_screen import PlayerScreen
from kivy.config import Config

Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.write()


class WindowManager(ScreenManager):
    pass


class MyMainApp(MDApp):
    def build(self):
        kv = Builder.load_file("main.kv")
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return kv

    def build_config(self, config):
        pass

    def build_settings(self, settings):
        pass

    def on_config_change(self, config, section, key, value):
        pass

    def on_stop(self):
        audio_player = self.root.ids.player_screen.audio_player
        audio_player.save_last_played_timestamp()
        audio_player.disable_saving = True
        if audio_player.playback.playing:
            audio_player.toggle_play()
        audio_player.playback.stop()


if __name__ == "__main__":
    MyMainApp().run()
