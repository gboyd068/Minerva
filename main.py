from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.settings import SettingsWithSidebar

from src.library_screen import LibraryScreen
from src.player_screen import PlayerScreen


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


if __name__ == "__main__":
    MyMainApp().run()
