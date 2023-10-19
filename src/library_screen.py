from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.app import App


class LibraryEntry(Button):
    def library_entry_selected(self):
        # add code for loading the selected book
        self.parent.parent.parent.parent.current = "player"


class LibraryScreen(Screen):
    pass
