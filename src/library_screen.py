from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivymd.app import MDApp


class LibraryEntry(Button):
    def library_entry_selected(self):
        # add code for loading the selected book
        app = MDApp.get_running_app()
        app.root.current = "player"


class LibraryScreen(Screen):
    pass

    # get books from files

    # create a library entry for each book