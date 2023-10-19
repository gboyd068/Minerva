from kivymd.uix.label import MDLabel
from bs4 import BeautifulSoup
from ebooklib import epub


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
        self.start_page_paragraph_pos = 0
        self.end_page_paragraph_pos = 0
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
                                self.end_page_paragraph_pos = last_line_pos + len(final_line) + 1
                            else:
                                self.end_page_paragraph_pos = 0
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
                            count += 1
                            paragraphs = page_text.split("\n")
                            first_line = cached_lines[0].words[0].text
                            # get position of first line in first paragraph
                            first_line_pos = paragraphs[-count].rfind(first_line)
                            print(first_line_pos)
                            if first_line_pos >= 0:
                                self.start_page_paragraph_pos = first_line_pos
                            else:
                                self.start_page_paragraph_pos = 0
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

        if start < 0:
            start = 0
        if end > len(paragraphs):
            end = len(paragraphs)

        if not prev and 0 < len(paragraphs) and len(paragraphs) > start:
            paragraphs[start] = paragraphs[start][self.start_page_paragraph_pos:]

        if prev and 0 < len(paragraphs) and len(paragraphs) > end:
            paragraphs[end] = paragraphs[end][:self.end_page_paragraph_pos]

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
        self.end_page_paragraph_pos = self.start_page_paragraph_pos
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
        self.start_page_paragraph_pos = self.end_page_paragraph_pos
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


