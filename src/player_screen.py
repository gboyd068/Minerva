from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.core.window import Window
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock

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


class ReaderWindow(MDLabel):
    def on_size(self, *args):
        pass
        # self.display_page()

        
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
        self.paragraph_within_chapter = 0  # paragraph number within chapter
        self.position_within_paragraph = 0  # character number within paragraph
        self.position_within_paragraph_next = 0
        self.page_buffer = 10
        self.load_epub()
        self.display_page()

    def generate_book_items_list(self, book):
        ordered_items = [id
                         for (ii, (id, show)) in enumerate(book.spine)]
        return [book.get_item_with_id(item) for item in ordered_items]

    def load_epub(self):
        self.book = epub.read_epub(self.epub_file)
        self.book_items_list = self.generate_book_items_list(self.book)
        self.num_book_items = len(self.book_items_list)

    def update_page_buffer(self, page_text, prev=False):
        if not prev:
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
            # deal with situation where the last line is part of an incomplete paragraph
            # page_text = self.get_page_text(self.get_chapter_text(
                # self.book_items_list[self.current_item_index]))
            if len(cached_lines) > 0:
                if len(cached_lines[-1].words) > 0:
                    if len(page_text.split()) > 0:
                        final_word = cached_lines[-1].words[-1].text.split()[-1]
                        if  final_word != page_text.split()[-1]:
                            count -= 1
                            paragraphs = page_text.split("\n")
                            final_line = cached_lines[-1].words[-1].text
                            # get position of last line in last paragraph
                            last_line_pos = paragraphs[count].rfind(final_line)
                            if last_line_pos >= 0:
                                self.position_within_paragraph = last_line_pos + len(final_line) + 1
                            else:
                                self.position_within_paragraph = 0
            self.page_buffer = count
        
        # if going back a page we need to calculate it the other way around
        if prev:
            # Calculate number of paragraphs that are started in the window
            count = 0
            # lines that are currently being drawn to text_label
            cached_lines = self._label._cached_lines
            for line in cached_lines[::-1]:
                if not line.line_wrap:  # if the line is not a wrapping of another line
                    count += 1

            if len(cached_lines) > 0:
                if len(cached_lines[0].words) > 0:
                    if len(page_text.split()) > 0:
                        first_word = cached_lines[0].words[0].text.split()[0]
                        if  first_word != page_text.split()[0]:
                            paragraphs = page_text.split("\n")
                            first_line = cached_lines[0].words[0].text
                            # get position of first line in first paragraph
                            first_line_pos = paragraphs[-(count+1)].rfind(first_line)
                            print(first_line_pos)
                            if first_line_pos >= 0:
                                self.position_within_paragraph = first_line_pos
                            else:
                                self.position_within_paragraph = 0
            self.page_buffer = count


    def display_page(self, prev=False):
        self.page_buffer = 50  # large number to ensure page is filled
        if prev:
            self.valign = "bottom"
            start = self.paragraph_within_chapter - self.page_buffer
            end = self.paragraph_within_chapter
        else:
            self.valign = "top"
            start = self.paragraph_within_chapter
            end = start+self.page_buffer
        if 0 <= self.current_item_index < self.num_book_items:
            item = self.book_items_list[self.current_item_index]
            # if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapter_text = self.get_chapter_text(item)
            # get lines between self.paragraph_within_chapter and self.paragraph_within_chapter + self.page_buffer
            page_text = self.get_page_text(chapter_text, start, end, prev)
            self.text = page_text
            self.texture_update()
            self.update_page_buffer(page_text, prev)
            if prev:
                self.valign = "bottom"
                start = self.paragraph_within_chapter - self.page_buffer
                end = self.paragraph_within_chapter
                page_text = self.get_page_text(chapter_text, start, end, prev)
            self.text = page_text
            self.texture_update()

    def get_page_text(self, chapter_text, start, end, prev):
        # get paragraphs between self.paragraph_within_chapter and self.paragraph_within_chapter + self.page_buffer
        # start = self.paragraph_within_chapter
        # end = start+self.page_buffer
        paragraphs = chapter_text.splitlines()
        # fix first line using position_within_paragraph
        if start < 0:
            start = 0
        if end > len(paragraphs):
            end = len(paragraphs)
        if 0 < len(paragraphs) and len(paragraphs) > start and not prev:
            paragraphs[start] = paragraphs[start][self.position_within_paragraph:]
        if prev and 0 < len(paragraphs) and len(paragraphs) > end:
            paragraphs[end] = paragraphs[end][:self.position_within_paragraph]
        page = "\n".join(
            paragraphs[start:end])
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
        self.page_buffer = 50
        if self.current_item_index > 0:
            if self.paragraph_within_chapter == 0: #  self.page_buffer:
                # go to previous chapter
                self.current_item_index -= 1
                self.paragraph_within_chapter = self.get_chapter_length(chapter) - 1
                            
            self.display_page(prev=True)
            self.paragraph_within_chapter -= self.page_buffer
            if self.paragraph_within_chapter < 0:
                self.paragraph_within_chapter = 0

            

    def next_page(self):
        chapter = self.book_items_list[self.current_item_index]
        if self.current_item_index < self.num_book_items - 1:
            if self.paragraph_within_chapter + self.page_buffer >= self.get_chapter_length(chapter):
                # go to next chapter
                self.current_item_index += 1
                self.paragraph_within_chapter = 0
            else:
                self.paragraph_within_chapter += self.page_buffer
            self.display_page()

    # def compute_pages(self):
    #     # compute all pages in the book
    #     self.pages = []
    #     while self.current_item_index < self.num_book_items - 1:
    #         self.pages.append(self._label._cached_lines)
    #         self.next_page()
    #     print("done")

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
