from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.core.window import Window


class PlayerScreen(Screen):
    def show_audio_toolbar(self):
        if self.ids.audio_toolbar.y < 0:
            Animation(y=0, duration=0.2).start(self.ids.audio_toolbar)
        else:
            Animation(y=-self.ids.audio_toolbar.height,
                      duration=0.2).start(self.ids.audio_toolbar)

    def show_top_toolbar(self):
        window_down_y = Window.height - self.ids.top_toolbar.height
        if self.ids.top_toolbar.y > window_down_y:
            Animation(y=window_down_y, duration=0.2).start(
                self.ids.top_toolbar)
        else:
            Animation(y=Window.height,
                      duration=0.2).start(self.ids.top_toolbar)
