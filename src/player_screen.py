from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty

from bs4 import BeautifulSoup
from ebooklib import epub


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
        if self.resize_reader_window:
            if self.is_active:
                Animation(size=(Window.width, Window.height - self.height),
                          duration=self.duration).start(self.parent.parent.ids.reader_window)
            else:
                Animation(size=(Window.width, Window.height),
                          duration=self.duration).start(self.parent.parent.ids.reader_window)


class AudioToolbarButton(MDIconButton):
    pass


class ReaderWindow(MDLabel):

    def on_size(self, *args):
        self.display_page()

        
    def on_touch_down(self, touch):
        # logic for clicking on the reader window
        top_toolbar = self.parent.ids.top_toolbar
        if top_toolbar.is_active:
            top_toolbar.toggle_toolbar()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.epub_file = "src/alloy.epub"
        self.book = None
        self.current_item_index = 0
        self.book_items_list = []
        self.num_book_items = 0
        self.scroll_view = None
        self.pages = []
        self.position_within_chapter = 0  # line number within chapter
        self.page_buffer = 10
        self.load_epub()
        self.display_page()

    def generate_book_items_list(self, book):
        ordered_items = [id
                         for (ii, (id, show)) in enumerate(book.spine)]

        # # get ids of all text items
        # text_item_names = []
        # for item in book.get_items():
        #     text_item_names.append(item.get_name()[5:])

        # # remove items from ordered_items that are not in text_item_names
        # ordered_items = [
        #     item for item in ordered_items if item in text_item_names]

        return [book.get_item_with_id(item) for item in ordered_items]

    def load_epub(self):
        self.book = epub.read_epub(self.epub_file)
        self.book_items_list = self.generate_book_items_list(self.book)
        self.num_book_items = len(self.book_items_list)

    def update_page_buffer(self):
        # Calculate number of real lines that are in the window
        count = 0
        # lines that are currently being drawn to text_label
        cached_lines = self._label._cached_lines
        # for line in cached_lines:
        #     for word in line.words:
        #         print(word.text)
        if len(cached_lines) == 0:
            self.page_buffer = 50
            return
        for line in cached_lines:
            if not line.line_wrap:  # if the line is not a wrapping of another line
                count += 1
        if cached_lines[-1].line_wrap:
            count -= 1
        # deal with situation where the last line is an incomplete line
        page_text = self.get_page_text(self.get_chapter_text(
            self.book_items_list[self.current_item_index]))
        if len(cached_lines) > 0:
            if len(cached_lines[-1].words) > 0:
                if len(page_text.split()) > 0:
                    if cached_lines[-1].words[-1].text != page_text.split()[-1]:
                        count -= 1
                # need to split paragraph in this case so that there isnt a repeat of text on the next page
        self.page_buffer = count

    def display_page(self):
        print("displaying page")
        if 0 <= self.current_item_index < self.num_book_items:
            item = self.book_items_list[self.current_item_index]
            # if item.get_type() == ebooklib.ITEM_DOCUMENT:
            self.page_buffer = 50  # large number to ensure page is filled
            chapter_text = self.get_chapter_text(item)
            # get lines between self.position_within_chapter and self.position_within_chapter + self.page_buffer
            page_text = self.get_page_text(chapter_text)
            self.text = page_text
            self.texture_update()
            self.update_page_buffer()
            page_text = self.get_page_text(chapter_text)
            self.text = page_text
            self.texture_update()

    def get_page_text(self, chapter_text):
        # get lines between self.position_within_chapter and self.position_within_chapter + self.page_buffer
        start = self.position_within_chapter
        end = start+self.page_buffer
        lines = chapter_text.splitlines()
        if end > len(lines):
            end = len(lines)
        page = "\n".join(
            lines[start:])
        return page

    def get_chapter_text(self, item):
        # Use BeautifulSoup to parse and extract HTML content
        soup = BeautifulSoup(item.content, "html.parser")
        chapter_text = soup.get_text()
        return chapter_text

    def get_chapter_length(self, item):
        return len(self.get_chapter_text(item).splitlines())

    def prev_page(self):
        chapter = self.book_items_list[self.current_item_index]
        self.update_page_buffer()
        if self.current_item_index > 0:
            if self.position_within_chapter < self.page_buffer:
                # go to previous chapter
                self.current_item_index -= 1
                self.position_within_chapter = self.get_chapter_length(
                    chapter) - self.page_buffer
            else:
                self.position_within_chapter -= self.page_buffer

            self.display_page()

    def next_page(self):
        chapter = self.book_items_list[self.current_item_index]
        # print(chapter)
        # print(self.get_chapter_length(chapter))
        # print(self.page_buffer)
        if self.current_item_index < self.num_book_items - 1:
            if self.position_within_chapter + self.page_buffer >= self.get_chapter_length(chapter):
                # go to next chapter
                self.current_item_index += 1
                self.position_within_chapter = 0
            else:
                self.position_within_chapter += self.page_buffer
            self.display_page()


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
