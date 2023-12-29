from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.clock import Clock
import os
import glob
import json
import pathlib
from ebooklib import epub


class LibraryEntry(MDCard):
    def __init__(self, book_path, book_title, book_author, percentage,**kwargs):
        super().__init__(**kwargs)
        self.book_path = book_path
        self.add_widget(MDLabel(text=book_title, halign="center", font_style="H6"))
        self.add_widget(PercentageLabel(percentage=percentage))

    def library_entry_selected(self):
        # add code for loading the selected book
        app = MDApp.get_running_app()
        app.root.player_screen.sync_script.load_book(self.book_path)
        Clock.schedule_once(self.go_to_player_screen)

    def go_to_player_screen(self, dt):
        app = MDApp.get_running_app()
        app.root.current = "player"


class PercentageLabel(MDLabel):
    def __init__(self, percentage, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{percentage}%"


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
        audio_files.sort()
        sub_files = glob.glob(os.path.join(directory, "subs", "*.srt"))
        sub_files.sort()

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
    
    def get_last_played_timestamp(self, timestamp_path):
        try:
            with open(timestamp_path, "r") as file:
                timestamp = json.load(file)
                audio_index = timestamp["audio_file_idx"]
                audio_position = timestamp["audio_position"]
                percentage_through_book = timestamp["percentage_through_book"]
                return audio_index, audio_position, percentage_through_book
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return 0, 0, 0

    
    def load_library(self):
        self.ids.library_scroll_layout.clear_widgets()
        entries = glob.glob(os.path.join(self.library_path, "*"))
        entries.sort()
        subdirs = [entry for entry in entries if os.path.isdir(entry)]
        for subdir in subdirs:
            dir_check_result = self.check_directory_in_library(subdir)
            if dir_check_result:
                self.add_library_entry(subdir)

    def add_library_entry(self, book_path):
        # get the metadata from the epub file
        book = epub.read_epub(glob.glob(os.path.join(book_path, "*.epub"))[0])
        book_title = book.get_metadata("DC", "title")
        book_author = book.get_metadata("DC", "creator")
        # cover?
        if len(book_title) != 0:
            book_title = book_title[0][0]
        if len(book_author) != 0:
            book_author = book_author[0][0]

        # get percentage through
        book_dir_name = str(pathlib.Path(book_path))
        user_data_dir = MDApp.get_running_app().user_data_dir
        timestamp_path = os.path.join(user_data_dir, book_dir_name,
                                           "last_played_timestamp.json")
        audio_index, audio_position, percentage_through_book = self.get_last_played_timestamp(timestamp_path)


        if book_title is None:
            book_title = os.path.basename(book_path)
        if book_author is None:
            book_author = "Unknown Author"
        entry_widget = LibraryEntry(book_path, book_title=book_title, book_author=book_author, percentage=percentage_through_book)
        self.ids.library_scroll_layout.add_widget(entry_widget)