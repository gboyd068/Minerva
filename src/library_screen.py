from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivymd.app import MDApp
from kivy.clock import Clock
import os
import glob


class LibraryEntry(Button):
    def __init__(self, book_path, **kwargs):
        super().__init__(**kwargs)
        self.book_path = book_path
        # load how far through the book the user is etc

    def library_entry_selected(self):
        # add code for loading the selected book
        app = MDApp.get_running_app()
        app.root.ids.player_screen.sync_script.load_book(self.book_path)
        Clock.schedule_once(self.go_to_player_screen)

    def go_to_player_screen(self, dt):
        app = MDApp.get_running_app()
        app.root.current = "player"

class LibraryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        app = MDApp.get_running_app()
        self.library_path = app.config.get("General", "library_path")
        Clock.schedule_once(self._finish_init)
    
    def _finish_init(self, dt):
        self.load_library()

    def check_directory_in_library(self, directory):
        audio_files = glob.glob(os.path.join(directory, "audio", "*.mp3"))
        sub_files = glob.glob(os.path.join(directory, "subs", "*.srt"))

        if len(audio_files) == 0 or len(sub_files) == 0:
            return False
        if len(audio_files) != len(sub_files):
            return False
        
        epub_file = glob.glob(os.path.join(directory, "*.epub"))
        if len(epub_file) == 0 or len(epub_file) > 1:
            return False
        if len(epub_file) == 1:
            epub_file = epub_file[0]

        return True

    
    def load_library(self):
        entries = glob.glob(os.path.join(self.library_path, "*"))
        subdirs = [entry for entry in entries if os.path.isdir(entry)]
        for subdir in subdirs:
            dir_check_result = self.check_directory_in_library(subdir)
            if dir_check_result:
                self.add_library_entry(subdir)

    def add_library_entry(self, book_path):
        self.ids.library_scroll_layout.add_widget(LibraryEntry(book_path))