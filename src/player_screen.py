from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.label import Label
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty


class PlayerScreen(Screen):
    pass


class MyToolbar(BoxLayout):
    # give the toolbar properties that can be used to animate it
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_active = BooleanProperty(False)
        self.resize_reader_window = BooleanProperty(False)
        self.inactive_y = NumericProperty(0)
        self.active_y = NumericProperty(0)
        self.duration = NumericProperty(0.2)

    def toggle_toolbar(self):
        if self.is_active:
            Animation(y=self.inactive_y,
                      duration=self.duration).start(self)
        else:
            Animation(y=self.active_y, duration=self.duration).start(
                self)
        self.is_active = not self.is_active

        # if the toolbar is meant to resize the reader window, do so
        if self.resize_reader_window:
            if self.is_active:
                Animation(size=(Window.width, Window.height - self.height),
                          duration=self.duration).start(self.parent.parent.ids.reader_window)
            else:
                Animation(size=(Window.width, Window.height),
                          duration=self.duration).start(self.parent.parent.ids.reader_window)


class BottomToolbarButton(MDIconButton):
    pass


class ReaderWindow(Label):
    def on_touch_down(self, touch):
        # logic for clicking on the reader window
        top_toolbar = self.parent.ids.top_toolbar
        if top_toolbar.is_active:
            top_toolbar.toggle_toolbar()


class TransparentButton(Button):
    # button class that is designed to be transparent and disablable depending on the current state
    pass
