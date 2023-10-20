from kivymd.uix.label import MDLabel
from bs4 import BeautifulSoup
from ebooklib import epub
from kivy.core.window import Window

class ReaderWindow(MDLabel):
    def on_size(self, *args):
        self.update_my_max_lines()
        # self.display_page()

    def update_my_max_lines(self):
        temp_text = self.text
        self.text = "a\n" * 1000
        self.texture_update()
        self.my_max_lines = len(self._label._cached_lines)
        self.text = temp_text
        self.texture_update()

        
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
        self.my_max_lines = 35 # needs to be set properly
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
        # lines that are currently being drawn to text_label
        self.update_my_max_lines()
        cached_lines = self._label._cached_lines
        paragraphs = page_text.split("\n")
        start_paragraph_complete = False
        end_paragraph_complete = False
        if len(cached_lines) == 0:
            self.page_buffer = 50
            return
        
        # get the positions within the paragraphs at the start and end of the page

        # position within paragraph at the start
        start_paragraph_idx = 0
        if len(cached_lines) > 0:
            if len(cached_lines[0].words) > 0:
                if len(page_text.split()) > 0:
                    if len(cached_lines[0].words[0].text.split()) > 0:
                        first_word = cached_lines[0].words[0].text.split()[0]
                        first_line = cached_lines[0].words[0].text
                        # find the paragraph which contains the first line
                        for i, paragraph in enumerate(paragraphs):
                            if first_line in paragraph:
                                start_paragraph_idx = i
                                break
                        if  first_word != page_text.split()[0]:
                            # get position of first line in that paragraph
                            self.start_page_paragraph_pos = paragraphs[start_paragraph_idx].rfind(first_line)
                        else:
                            start_paragraph_complete = True
                            self.start_page_paragraph_pos = 0

        # position within paragraph at the end
        end_paragraph_idx = 0
        if len(cached_lines) > 0:
            if len(cached_lines[-1].words) > 0:
                if len(page_text.split()) > 0:
                    print("getting end paragraph idx")
                    final_word = cached_lines[-1].words[-1].text.split()[-1]
                    final_line = cached_lines[-1].words[-1].text
                    # find the paragraph which contains the final line
                    for i, paragraph in enumerate(paragraphs): # THIS CAN FAIL
                        if final_line in paragraph:
                            end_paragraph_idx = i
                            break
                        end_paragraph_idx = i
                    if  final_word != page_text.split()[-1]:
                        # get position of final line in that paragraph
                        last_line_pos = paragraphs[end_paragraph_idx].rfind(final_line)
                        if last_line_pos >= 0:
                            self.end_page_paragraph_pos = last_line_pos + len(final_line) + 1
                        else:
                            self.end_page_paragraph_pos = 0
                    else:
                        end_paragraph_complete = True
                        self.end_page_paragraph_pos = 0
        
        print("num_cached_lines", len(cached_lines))
        if len(cached_lines) < self.my_max_lines:
            # page not full, go back / forward a chapter by setting the page buffer to a large number
            end_paragraph_idx = 50
            self.valign = "top"
            self.start_page_paragraph_pos = 0
        
        backward_count = 0
        for line in cached_lines[::-1]:
            if not line.line_wrap:  # if the line is not a wrapping of another line
                backward_count += 1


        if prev:
            end_paragraph_idx = len(paragraphs) - 1

        print("start_paragraph_idx", start_paragraph_idx)
        print("end_paragraph_idx", end_paragraph_idx)
        print("start_paragraph_complete", start_paragraph_complete)
        print("end_paragraph_complete", end_paragraph_complete)
        print("forward_count", backward_count)
        if not prev:
            self.page_buffer = end_paragraph_idx - start_paragraph_idx
            # if going forward and final paragraph complete then increase page buffer
            if end_paragraph_complete:
                self.page_buffer += 1
        else:
            self.page_buffer = end_paragraph_idx - start_paragraph_idx
            # if the first paragraph is complete then increase page buffer
            if start_paragraph_complete:
                self.page_buffer += 1
        print("page buffer", self.page_buffer)

        if start_paragraph_idx == 0 and end_paragraph_idx == 0:
            self.page_buffer = 50



    def display_page(self, prev=False):
        self.page_buffer = 50  # large number to ensure page is filled
        if prev:
            self.valign = "bottom"
            start = self.paragraph_within_chapter - self.page_buffer + 1
            end = self.paragraph_within_chapter + 1
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
            page_text_no_cutoff = self.get_page_text(chapter_text, start, end, prev, cuttoff=False)
            self.text = page_text
            self.texture_update()
            self.update_page_buffer(page_text_no_cutoff, prev)
            # if prev:
            #     self.valign = "bottom"
            #     start = self.paragraph_within_chapter - self.page_buffer
            #     end = self.paragraph_within_chapter
            #     page_text = self.get_page_text(chapter_text, start, end, prev)
            self.text = page_text
            self.texture_update()

    def get_page_text(self, chapter_text, start, end, prev, cuttoff=True):
        # get paragraphs between self.paragraph_within_chapter and self.paragraph_within_chapter + self.page_buffer
        # start = self.paragraph_within_chapter
        # end = start+self.page_buffer
        paragraphs = chapter_text.splitlines()

        if start < 0:
            start = 0
        if end > len(paragraphs):
            end = len(paragraphs)

        if cuttoff:
            if not prev and 0 < len(paragraphs) and len(paragraphs) > start:
                paragraphs[start] = paragraphs[start][self.start_page_paragraph_pos:]

            if prev and 0 < len(paragraphs) and len(paragraphs) > end:
                paragraphs[end-1] = paragraphs[end-1][:self.end_page_paragraph_pos]

        page = "\n".join(
            paragraphs[start:end])
        
        # page = page.strip("\n")
        return page.strip("\n")

    def get_chapter_text(self, item):
        # Use BeautifulSoup to parse and extract HTML content
        soup = BeautifulSoup(item.content, "html.parser")
        chapter_text = soup.get_text()
        return chapter_text.strip("\n")

    def get_chapter_length(self, item):
        return len(self.get_chapter_text(item).splitlines())

    def prev_page(self):
        self.end_page_paragraph_pos = self.start_page_paragraph_pos
        chapter = self.book_items_list[self.current_item_index]
        self.page_buffer = 50
        if self.current_item_index > 0:
            if self.paragraph_within_chapter == 0:
                # go to previous chapter
                self.current_item_index -= 1
                self.paragraph_within_chapter = self.get_chapter_length(chapter) - 1
            
            print("------------\nparagraph within chapter", self.paragraph_within_chapter)
            self.display_page(prev=True)
            self.paragraph_within_chapter -= self.page_buffer
            if self.paragraph_within_chapter < 0:
                self.paragraph_within_chapter = 0
            # hmmm
            if self.paragraph_within_chapter  > self.get_chapter_length(chapter) - 1:
                self.paragraph_within_chapter = self.get_chapter_length(chapter) - 1


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


