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
        self.chapter_label = None
        self.scroll_view = None

    def build(self):
        self.load_epub()
        self.book_items_list = self.generate_book_items_list(self.book)
        self.num_book_items = len(self.book_items_list)
        return self.create_ui()

    def generate_book_items_list(self, book):
        ordered_items = [id
                         for (ii, (id, show)) in enumerate(book.spine)]

        # get ids of all text items
        text_item_names = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            text_item_names.append(item.get_name()[5:])

        # remove items from ordered_items that are not in text_item_names
        ordered_items = [
            item for item in ordered_items if item in text_item_names]

        return [book.get_item_with_id(item) for item in ordered_items]

    def load_epub(self):
        self.book = epub.read_epub(self.epub_file)
        # use ebooklib to print all of the filenames in the EPUB

    def create_ui(self):
        # Create the main layout
        main_layout = BoxLayout(orientation="vertical")

        # Create a ScrollView to hold the content
        self.scroll_view = ScrollView()

        # Create a Label to display the chapter content
        self.chapter_label = Label(
            markup=True,
            size_hint_y=None,
            halign='left',
            valign='top',
            padding=(0, 0),  # Adjust padding as needed
            text_size=(Window.width - 200, None),  # Set text_size to wrap text
        )
        self.chapter_label.bind(texture_size=self.chapter_label.setter('size'))

        # Create a Button layout for navigation
        button_layout = BoxLayout(size_hint=(1, 0.1))
        prev_button = Button(text="Previous", on_press=self.prev_chapter)
        next_button = Button(text="Next", on_press=self.next_chapter)
        button_layout.add_widget(prev_button)
        button_layout.add_widget(next_button)

        # Add the Label and Button layouts to the main layout
        main_layout.add_widget(self.scroll_view)
        self.scroll_view.add_widget(self.chapter_label)
        main_layout.add_widget(button_layout)

        # Display the first chapter
        self.display_chapter(self.chapter_label)

        return main_layout

    def display_chapter(self, label):
        if 0 <= self.current_item_index < self.num_book_items:
            item = self.book_items_list[self.current_item_index]
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Use BeautifulSoup to parse and extract HTML content
                soup = BeautifulSoup(item.content, "html.parser")
                chapter_text = soup.get_text()
                label.text = chapter_text

    def prev_chapter(self, instance):
        if self.current_item_index > 0:
            self.current_item_index -= 1
            self.display_chapter(self.chapter_label)

            # Scroll to the bottom of the ScrollView
            self.scroll_view.scroll_y = 0.0

    def next_chapter(self, instance):
        if self.current_item_index < self.num_book_items - 1:
            self.current_item_index += 1
            self.display_chapter(self.chapter_label)

            # Scroll to the top of the ScrollView
            self.scroll_view.scroll_y = 1.0


if __name__ == "__main__":
    epub_file_path = "epub.epub"  # Replace with the path to your EPUB file
    EPUBReaderApp(epub_file_path).run()
