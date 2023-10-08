import math
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView


class EPUBReaderApp(App):
    def __init__(self, epub_file):
        super(EPUBReaderApp, self).__init__()
        self.epub_file = epub_file
        self.book = None
        self.current_item_index = 0
        self.book_items_list = []
        self.num_book_items = 0
        self.text_label = None
        self.scroll_view = None
        self.pages = []
        self.position_within_chapter = 0  # line number within chapter
        self.page_buffer = 10

    def build(self):
        self.load_epub()
        return self.create_ui()

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

    def create_ui(self):
        # Create the main layout
        main_layout = BoxLayout(orientation="vertical")

        # Create a Label to display the chapter content
        self.text_label = Label(
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top',
            padding=(0, 0),  # Adjust padding as needed),
            text_size=(Window.width, Window.height-10),
        )
        self.text_label.bind(texture_size=self.text_label.setter('size'))

        # Create a Button layout for navigation
        button_layout = BoxLayout(size_hint=(1, 0.1))
        prev_button = Button(text="Previous", on_press=self.prev_page)
        next_button = Button(text="Next", on_press=self.next_page)
        button_layout.add_widget(prev_button)
        button_layout.add_widget(next_button)

        # Add the Label and Button layouts to the main layout
        main_layout.add_widget(self.text_label)
        main_layout.add_widget(button_layout)

        # Display the first chapter
        self.display_page(self.text_label)

        return main_layout

    def update_page_buffer(self, label):
        # Calculate number of lines that can fit in the window
        font_size = self.text_label.font_size
        max_line_length = self.get_maximum_line_length(label)
        if max_line_length == 0:
            self.page_buffer = 10
            return
        chapter_text = self.get_chapter_text(
            self.book_items_list[self.current_item_index])

        self.page_buffer = 20

    def get_maximum_line_length(self, label):
        label_text_displayed = label._label.label
        # get maximum line length
        max_line_length = 0
        for line in label_text_displayed.splitlines():
            max_line_length = max(max_line_length, len(line))
        return max_line_length

    def display_page(self, label):
        if 0 <= self.current_item_index < self.num_book_items:
            item = self.book_items_list[self.current_item_index]
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                self.update_page_buffer(label)
                chapter_text = self.get_chapter_text(item)
                # get lines between self.position_within_chapter and self.position_within_chapter + self.page_buffer
                page_text = self.get_page_text(chapter_text, self.position_within_chapter,
                                               self.position_within_chapter + self.page_buffer)
                label.text = page_text

    def get_page_text(self, chapter_text, start, end):
        # get lines between self.position_within_chapter and self.position_within_chapter + self.page_buffer
        lines = chapter_text.splitlines()
        if end > len(lines):
            end = len(lines)
        page = "\n".join(lines[start:end])
        return page

    def get_chapter_text(self, item):
        # Use BeautifulSoup to parse and extract HTML content
        soup = BeautifulSoup(item.content, "html.parser")
        chapter_text = soup.get_text()
        return chapter_text

    def get_chapter_length(self, item):
        return len(self.get_chapter_text(item).splitlines())

    def prev_page(self, instance):
        chapter = self.book_items_list[self.current_item_index]
        if self.current_item_index > 0:
            if self.position_within_chapter < self.page_buffer:
                # go to previous chapter
                self.current_item_index -= 1
                self.position_within_chapter = self.get_chapter_length(
                    chapter) - self.page_buffer
            else:
                self.position_within_chapter -= self.page_buffer
            # display page
            self.display_page(self.text_label)

            # Scroll to the bottom of the ScrollView
            # self.scroll_view.scroll_y = 0.0

    def next_page(self, instance):
        chapter = self.book_items_list[self.current_item_index]
        if self.current_item_index < self.num_book_items - 1:
            if self.position_within_chapter + self.page_buffer >= self.get_chapter_length(chapter):
                # go to next chapter
                self.current_item_index += 1
                self.position_within_chapter = 0
            else:
                self.position_within_chapter += self.page_buffer

            # display page
            self.display_page(self.text_label)

            # Scroll to the top of the ScrollView
            # self.scroll_view.scroll_y = 1.0


if __name__ == "__main__":
    epub_file_path = "epub.epub"  # Replace with the path to your EPUB file
    EPUBReaderApp(epub_file_path).run()
