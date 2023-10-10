from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.label import Label


class PlayerScreen(Screen):
    def toggle_audio_toolbar(self):
        duration = 0.2
        if self.ids.audio_toolbar.y < 0:
            # move the audio toolbar up
            Animation(y=0, duration=duration).start(self.ids.audio_toolbar)
            # move the reader window up to make room for the audio toolbar
            Animation(size=(Window.width, Window.height - self.ids.audio_toolbar.height),
                      duration=duration).start(self.ids.reader_window)
        else:
            Animation(y=-self.ids.audio_toolbar.height,
                      duration=duration).start(self.ids.audio_toolbar)
            # move the reader window down
            Animation(size=(Window.width, Window.height),
                      duration=duration).start(self.ids.reader_window)

    def toggle_top_toolbar(self):
        window_down_y = Window.height - self.ids.top_toolbar.height
        if self.ids.top_toolbar.y > window_down_y:
            Animation(y=window_down_y, duration=0.2).start(
                self.ids.top_toolbar)
        else:
            Animation(y=Window.height,
                      duration=0.2).start(self.ids.top_toolbar)


class ReaderWindow(Label):
    pass


class TransparentButton(Button):
    # button class that is designed to be transparent and disablable depending on the current state
    pass
