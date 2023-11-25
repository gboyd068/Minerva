from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivymd.uix.button import MDIconButton
from kivymd.app import MDApp



from src.reader_window import ReaderWindow
from src.audio_player import AudioPlayer
from src.sync_script import SyncScript

class PlayerScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sync_script = None
        self.audio_player = None
        # CANT ACCESS IDS BECAUSE THEY HAVENT BEEN CREATED YET so do the rest of the init after this has been done
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, dt):
        reader_window = self.reader_window
        # make audio player and sync script members of the player screen so kivy can access them
        self.audio_player = AudioPlayer()
        self.sync_script = SyncScript(self.audio_player, reader_window)


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
            
            # reader_window.display_page()
            # Clock.schedule_once(reader_window.display_page, self.duration)
            # reader_window.texture_update()
            # print(reader_window.page_buffer)
            # chapter_text = reader_window.chapter_text

            # page_text_no_cutoff = self.get_page_text(chapter_text, start, end, prev, cuttoff=False)
            # reader_window.display_page()
            # print(reader_window.page_buffer)


class AudioToolbarButton(MDIconButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_player = None
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, dt):
        app = MDApp.get_running_app()
        self.audio_player = app.root.ids.player_screen.audio_player
        

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
