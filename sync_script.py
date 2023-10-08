import difflib
from epub_render import EPUBReaderApp
from kivytest import SubtitlePlayerApp


def binary_search(arr, x):
    left, right = 0, len(arr) - 1
    result = None  # Initialize result to None

    while left <= right:
        mid = left + (right - left) // 2

        # If the current element is smaller than or equal to x, update the result and search in the right half
        if arr[mid] <= x:
            result = arr[mid]
            left = mid + 1
        else:
            # If the current element is greater than x, search in the left half
            right = mid - 1

    return result


def time_from_bookpos(book_time_dict, bookpos):
    nearest_bookpos = binary_search(list(book_time_dict.keys()), bookpos)
    return book_time_dict[nearest_bookpos]


def bookpos_from_time(book_time_dict, time):
    nearest_time = binary_search(list(book_time_dict.values()), time)
    index = list(book_time_dict.values()).index(nearest_time)
    return list(book_time_dict.keys())[index]


epub_file_path = "alloy.epub"  # Replace with the path to your EPUB file
epubapp = EPUBReaderApp(epub_file_path)
epubapp.run()

subtitle_file = "subtitle.srt"
audio_file = "audio.mp3"
player = SubtitlePlayerApp(subtitle_file, audio_file)
player.run()


booktext = ""
for item in epubapp.book_items_list:
    booktext += epubapp.get_chapter_text(item)
# remove newlines in booktext
booktext = booktext.replace('\n', ' ')

start_index = 0
book_time_dict = {}
for s in player.subtitle_file:

    text = s.text.replace('\n', ' ')
    # Create a SequenceMatcher object
    matcher = difflib.SequenceMatcher(None, booktext, text)

    # Find the best matching substring within the larger text
    match = matcher.find_longest_match(start_index, min(
        start_index+2000, len(booktext)), 0, len(text))

    if match.size > 0:
        # Start index of the best match
        start_index = match.a
        # End index of the best match
        end_index = match.a + match.size

        # print("Start index:", start_index)
        # print("End index:", end_index)
        # print("Best match:", booktext[start_index:end_index])
        book_time_dict[start_index] = player.subtitle_time_to_seconds(
            s.start.to_time())
    else:
        print("No match found.")


print(time_from_bookpos(book_time_dict, 58000))
print(bookpos_from_time(book_time_dict, 200))
