from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar, ConfigParser

from src.library_screen import LibraryScreen
from src.player_screen import PlayerScreen
from kivy.config import Config

from settingsjson import settings_json

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
        # load settings here
        config = ConfigParser()
        config.read('mymain.ini')
        self.theme_cls.theme_style = config.get('General', 'theme')
        return kv

    def build_config(self, config):
        config.setdefaults("General", 
                           {"library_path": "path",
                            "theme": "Light",
                            'boolexample': True,
                            }
                           )

    def build_settings(self, settings):
        settings.add_json_panel('General', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        # automatically called when a user changes a setting
        if key == "theme":
            # this isn't changing text colour properly etc
            self.theme_cls.theme_style = value

    def save_current_book_location(self):
        audio_player = self.root.ids.player_screen.audio_player
        if audio_player.playback is not None:
            audio_player.save_last_played_timestamp()

    def on_stop(self):
        self.save_current_book_location()
        audio_player = self.root.ids.player_screen.audio_player
        audio_player.disable_saving = True
        if audio_player.playback is not None:
            audio_player.playback.stop()


if __name__ == "__main__":
    MyMainApp().run()
