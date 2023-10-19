from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty

from src.reader_window import ReaderWindow

class PlayerScreen(Screen):
    def disable_buttons(self):
        top_toolbar_active = self.ids.top_toolbar.is_active
        audio_toolbar_active = self.ids.audio_toolbar.is_active
        if top_toolbar_active or audio_toolbar_active:
            self.ids.next_button.my_disabled = True
            self.ids.prev_button.my_disabled = True
        else:
            self.ids.next_button.my_disabled = False
            self.ids.prev_button.my_disabled = False

        self.ids.top_toolbar_show_button.my_disabled = top_toolbar_active

        self.ids.audio_toolbar_show_button.my_disabled = audio_toolbar_active


class MyToolbar(BoxLayout):
    # give the toolbar properties that can be used to animate it
    is_active = BooleanProperty(False)
    resize_reader_window = BooleanProperty(False)
    inactive_y = NumericProperty(0)
    active_y = NumericProperty(0)
    duration = NumericProperty(0.2)

    def on_is_active(self, instance, value):
        self.parent.parent.disable_buttons()

    def toggle_toolbar(self):
        if self.is_active:
            Animation(y=self.inactive_y,
                      duration=self.duration).start(self)
        else:
            Animation(y=self.active_y, duration=self.duration).start(
                self)
        self.is_active = not self.is_active

        # if the toolbar is meant to resize the reader window, do so
        reader_window = self.parent.parent.ids.reader_window
        if self.resize_reader_window:
            if self.is_active:
                Animation(size=(Window.width, Window.height - self.height),
                          duration=self.duration).start(reader_window)
            else:
                Animation(size=(Window.width, Window.height),
                          duration=self.duration).start(reader_window)
            reader_window.display_page()


class AudioToolbarButton(MDIconButton):
    pass

class TransparentButton(Button):
    # button class that is designed to be transparent and disablable depending on the current state
    my_disabled = BooleanProperty(False)
    default_size_x = NumericProperty(0)
    default_size_y = NumericProperty(0)

    def on_my_disabled(self, instance, value):
        if value:
            self.size = (0, 0)
            self.disabled = True
        else:
            self.size = (self.default_size_x, self.default_size_y)
            self.disabled = False
