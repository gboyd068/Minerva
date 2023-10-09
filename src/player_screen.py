from kivy.uix.screenmanager import Screen
from kivy.animation import Animation


class PlayerScreen(Screen):
    def show_toolbar(self):
        if self.ids.toolbar.y < 0:
            Animation(y=0, duration=0.2).start(self.ids.toolbar)
        else:
            Animation(y=-self.ids.toolbar.height,
                      duration=0.2).start(self.ids.toolbar)
