from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivymd.app import MDApp
from kivy.clock import Clock


class LibraryEntry(Button):
    def __init__(self, book_path=None, **kwargs):
        super().__init__(**kwargs)
        if book_path is None:
            self.book_path = "alloy"
        # self.book_path = book_path

    def library_entry_selected(self):
        # add code for loading the selected book
        app = MDApp.get_running_app()
        app.root.ids.player_screen.sync_script.load_book(self.book_path)
        Clock.schedule_once(self.go_to_player_screen)

    def go_to_player_screen(self, dt):
        app = MDApp.get_running_app()
        app.root.current = "player"

class LibraryScreen(Screen):
    pass

    # get books from files

    # create a library entry for each book