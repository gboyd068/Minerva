from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.settings import SettingsWithNoMenu
from kivymd.uix.button import MDIconButton
from kivymd.toast import toast
from plyer import filechooser

from src.library_screen import LibraryScreen
from src.player_screen import PlayerScreen
from settingsjson import settings_json


class WindowManager(ScreenManager):
    pass
    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
    #     self._keyboard.bind(on_key_down=self._on_keyboard_down)

    # def _keyboard_closed(self):
    #     self._keyboard.unbind(on_key_down=self._on_keyboard_down)
    #     self._keyboard = None

    # def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
    #     print(keycode)


class MySettings(SettingsWithNoMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = MDApp.get_running_app()
        close_button = MDIconButton(theme_icon_color="Custom", icon_color='white', icon="close", on_release=app.close_settings)
        self.add_widget(close_button, 0, 'before')

class MinervaApp(MDApp):
    def build(self):
        kv = Builder.load_file("main.kv")
        self.settings_cls = MySettings
        self.use_kivy_settings = False
        self.theme_cls.theme_style = self.config.get('General', 'theme')
        self.file_manager_open()
        return kv
    
    def file_manager_open(self):
        path = filechooser.choose_dir()[0] 
        # this method returns a list with the first index
        # being the path of the file selected
        toast(path)

    def build_config(self, config):
        config.adddefaultsection('General') 
        config.setdefault('General','library_path', '.')
        config.setdefault('General', 'theme', 'Light')
        config.setdefault('General','text_margin', 40)
        config.setdefault('General','font_size', 40)
        config.setdefault('General','skip_size', 30)
        config.setdefault('General','playback_speed', 1.0)

    def build_settings(self, settings):
        settings.add_json_panel('General', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        # automatically called when a user changes a setting
        self.config = config
        if key == "theme":
            self.theme_cls.theme_style = value 
        if key == "text_margin":
            value = int(value)
            self.root.ids.player_screen.ids.reader_window.padding = (value, value)
        if key == "font_size":
            value = int(value)
            self.root.ids.player_screen.ids.reader_window.font_size = value
        if key == "library_path":
            self.root.ids.library_screen.library_path = value
            self.root.ids.library_screen.load_library()
        if key == "playback_speed":
            audio_player = self.root.ids.player_screen.audio_player
            audio_player.playback_speed = float(value)
            if audio_player.playback is not None and audio_player.current_audio_idx is not None:
                audio_player.load_audio_file(audio_player.current_audio_idx, audio_player.current_audio_position)

    def save_current_book_location(self):
        audio_player = self.root.ids.player_screen.audio_player
        if audio_player.playback is not None:
            audio_player.save_last_played_timestamp()

    def on_stop(self): # only gets called on desktop, android doesn't call this (don't know about ios)
        self.save_current_book_location()
        audio_player = self.root.ids.player_screen.audio_player
        audio_player.disable_saving = True
        if audio_player.playback is not None:
            audio_player.playback.pause()


if __name__ == "__main__":
    MinervaApp().run()
