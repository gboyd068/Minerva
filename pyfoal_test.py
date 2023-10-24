import pyfoal
from ebooklib import epub
from bs4 import BeautifulSoup

def get_chapter_text(item):
        # Use BeautifulSoup to parse and extract HTML content
        soup = BeautifulSoup(item.content, "html.parser")
        chapter_text = soup.get_text()
        return chapter_text.strip("\n")

# Load epub
book = epub.read_epub('alloy/alloy.epub')
ordered_items = [id
                         for (ii, (id, show)) in enumerate(book.spine)]
ordered_items = [book.get_item_with_id(item) for item in ordered_items]
chapter_texts = [get_chapter_text(chapter) for chapter in ordered_items]

booktext = ""
chapter_starts = []
paragraph_starts = []
current_idx = 0
for chapter in chapter_texts:
    chapter_starts.append(current_idx)
    # get paragraph starts
    p_starts = []
    for paragraph in chapter.splitlines():
        p_starts.append(current_idx)
        booktext += paragraph + " "
        current_idx += len(paragraph) + 1
    paragraph_starts.append(p_starts)


# Load and resample audio
audio_file = 'alloy/audio/alloy1.mp3'
audio = pyfoal.load.audio(audio_file)

# Select an aligner. One of ['mfa', 'p2fa', 'radtts' (default)].
aligner = 'radtts'


# Select a GPU to run inference on
gpu = 0

alignment = pyfoal.align(
    booktext,
    audio,
    pyfoal.SAMPLE_RATE)

print(alignment)