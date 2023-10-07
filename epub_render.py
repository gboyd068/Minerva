import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window


class EPUBReaderApp(App):
    def __init__(self, epub_file):
        super(EPUBReaderApp, self).__init__()
        self.epub_file = epub_file
        self.book = None

    def build(self):
        self.load_epub()
        return self.create_ui()

    def load_epub(self):
        self.book = epub.read_epub(self.epub_file)

    def create_ui(self):
        # Create the main layout
        main_layout = BoxLayout(orientation="vertical")

        # Create a ScrollView to hold the content
        scroll_view = ScrollView()

        # Create a GridLayout to display chapters
        grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        # Iterate through the book's items (chapters) and display them
        for itemidx, item in enumerate(self.book.get_items()):
            if item.get_type() == ebooklib.ITEM_DOCUMENT and itemidx == 11:
                # Use BeautifulSoup to parse and extract HTML content
                soup = BeautifulSoup(item.content, "html.parser")
                chapter_text = soup.get_text()

                # Create a Label to display the chapter content
                chapter_label = Label(
                    text=chapter_text,
                    markup=True,
                    size_hint_y=None,
                    halign='left',
                    valign='top',
                    padding=(0, 0),  # Adjust padding as needed
                    # Set text_size to wrap text
                    text_size=(Window.width - 200, None),
                )
                chapter_label.bind(texture_size=chapter_label.setter('size'))
                grid_layout.add_widget(chapter_label)

        # Add the GridLayout to the ScrollView
        scroll_view.add_widget(grid_layout)

        # Add the ScrollView to the main layout
        main_layout.add_widget(scroll_view)

        return main_layout


if __name__ == "__main__":
    epub_file_path = "epub.epub"  # Replace with the path to your EPUB file
    EPUBReaderApp(epub_file_path).run()
