import glob
import os
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.settings import SettingsWithNoMenu
from kivymd.uix.button import MDIconButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
from kivy.utils import platform
from kivy.clock import Clock

if platform == "android":
    from jnius import autoclass
    from jnius import cast
    from android import activity
    from android.storage import primary_external_storage_path

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True,
        )
        self.primary_ext_storage = None
        self.permissions_external_storage()

    def build(self):
        kv = Builder.load_file("main.kv")
        self.settings_cls = MySettings
        self.use_kivy_settings = False
        self.theme_cls.theme_style = self.config.get('General', 'theme')
        if self.config.get('General', 'library_path') == "None":
            Clock.schedule_once(self.file_manager_open)
        return kv
        

    def permissions_external_storage(self, *args):                  
        if platform == "android":
            self.primary_ext_storage = primary_external_storage_path()
            self.PythonActivity = autoclass("org.kivy.android.PythonActivity")
            self.Environment = autoclass("android.os.Environment")
            self.Intent = autoclass("android.content.Intent")
            self.Settings = autoclass("android.provider.Settings")
            self.Uri = autoclass("android.net.Uri")
                # If you have access to the external storage, do whatever you need
            if self.Environment.isExternalStorageManager():
                # If you don't have access, launch a new activity to show the user the system's dialog
                # to allow access to the external storage
                pass
            else:
                try:
                    activity = self.PythonActivity.mActivity.getApplicationContext()
                    uri = self.Uri.parse("package:" + activity.getPackageName())
                    intent = self.Intent(self.Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, uri)
                    currentActivity = cast(
                    "android.app.Activity", self.PythonActivity.mActivity
                    )
                    currentActivity.startActivityForResult(intent, 101)
                except:
                    intent = self.Intent()
                    intent.setAction(self.Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                    currentActivity = cast(
                    "android.app.Activity", self.PythonActivity.mActivity
                    )
                    currentActivity.startActivityForResult(intent, 101)


    
    def file_manager_open(self,dt):
        dir = self.user_data_dir
        if self.primary_ext_storage is not None:
            dir = self.primary_ext_storage
        self.file_manager.show(dir)  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        self.exit_manager()
        print(glob.glob(os.path.join(path, "*"), recursive=True))
        self.config.set('General', 'library_path', path)
        self.config.write()
        self.root.library_screen.library_path = path
        self.root.library_screen.load_library()

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def build_config(self, config):
        config.adddefaultsection('General')
        config.setdefault('General','library_path', 'None')
        config.setdefault('General', 'theme', 'Light')
        config.setdefault('General','text_margin', 40)
        config.setdefault('General','font_size', 40)
        config.setdefault('General','skip_size', 30)
        config.setdefault('General','playback_speed', 1.0)
        config.setdefault('General','auto_page_turn', True)

    def build_settings(self, settings):
        settings.add_json_panel('General', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        # automatically called when a user changes a setting
        self.config = config
        if key == "theme":
            self.theme_cls.theme_style = value 
        if key == "text_margin":
            value = int(value)
            self.root.player_screen.reader_window.padding = (value, value)
            self.root.player_screen.reader_window.display_page()
        if key == "font_size":
            value = int(value)
            self.root.player_screen.reader_window.font_size = value
            self.root.player_screen.reader_window.display_page()
        if key == "library_path":
            self.root.library_screen.library_path = value
            self.root.library_screen.load_library()
        if key == "playback_speed":
            audio_player = self.root.player_screen.audio_player
            audio_player.enable_status_update = False
            audio_player.playback_speed = float(value)
            if audio_player.is_audio_loaded and audio_player.current_audio_idx is not None:
                audio_player.load_audio_file(audio_player.current_audio_idx, audio_player.current_audio_position)
            audio_player.enable_status_update = True
        if key == "auto_page_turn":
            self.root.player_screen.sync_script.auto_page_turn_enabled = not value=="0"

    def save_current_book_location(self):
        audio_player = self.root.player_screen.audio_player
        if audio_player.is_audio_loaded:
            audio_player.save_last_played_timestamp()

    def on_stop(self): # only gets called on desktop, android doesn't call this (don't know about ios)
        self.save_current_book_location()
        audio_player = self.root.player_screen.audio_player
        audio_player.disable_saving = True
        if audio_player.is_audio_loaded:
            audio_player.pause()

    def on_pause(self):
        # PROBABLY NEED TO CHANGE THIS AS IT WOULD DISABLE SAVING WHEN APP MINIMISED
        self.save_current_book_location()
        audio_player = self.root.player_screen.audio_player
        audio_player.disable_saving = True
        if audio_player.is_audio_loaded:
            audio_player.pause()
        return True
    
    def on_resume(self):
        audio_player = self.root.player_screen.audio_player
        audio_player.disable_saving = False
        return True

    


if __name__ == "__main__":
    MinervaApp().run()
