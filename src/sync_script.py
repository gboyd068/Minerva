import difflib
from epub_render import EPUBReaderApp
from audio_player import SubtitlePlayerApp
import os
import glob
import pysrt
from just_playback import Playback

def binary_search(arr, x, return_idx=False):
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

    if return_idx:
        if result is None:
            return 0
        return arr.index(result) # this is dumb but I couldn't be bothered
    if result is None:
        return arr[0]
    return result

def total_time_from_bookpos(book_time_dict, chapter_starts, paragraph_starts, bookpos):
    """takes in a book position as (chapter_idx, paragraph_idx, characters_through_paragraph) and returns the total time"""
    book_index = get_book_index(*bookpos, chapter_starts, paragraph_starts)
    book_index_list = list(book_time_dict.keys())
    nearest_book_index = binary_search(book_index_list, book_index)
    return book_time_dict[nearest_book_index]


def bookpos_from_total_time(book_time_dict, chapter_starts, paragraph_starts, total_time):
    """takes in a total time and returns a book position as (chapter_idx, paragraph_idx, characters_through_paragraph)"""
    nearest_time = binary_search(list(book_time_dict.values()), total_time)
    index = list(book_time_dict.values()).index(nearest_time)
    book_index = list(book_time_dict.keys())[index]
    bookpos = get_chapter_paragraph_position(book_index, chapter_starts, paragraph_starts)
    return bookpos

def get_total_time(audio_file_start_times, audio_file_index, time):
    """takes the current audio file index and the time in that file and returns the total time elapsed"""
    total_time = audio_file_start_times[audio_file_index] + time
    return total_time

def get_audio_file_index_and_file_time(audio_file_start_times, total_time):
    """takes the total time elapsed and returns the audio file index"""
    audio_file_index = binary_search(audio_file_start_times, total_time, True)
    file_time = total_time - audio_file_start_times[audio_file_index]
    return audio_file_index, file_time


def file_time_from_bookpos(book_time_dict, chapter_starts, paragraph_starts, audio_file_start_times, bookpos):
    """takes in a book position as (chapter_idx, paragraph_idx, characters_through_paragraph) and returns audio file and file time"""
    total_time = total_time_from_bookpos(book_time_dict, chapter_starts, paragraph_starts, bookpos)
    audio_file_index, file_time = get_audio_file_index_and_file_time(audio_file_start_times, total_time)
    return audio_file_index, file_time

def bookpos_from_file_time(book_time_dict, chapter_starts, paragraph_starts, audio_file_start_times, audio_file_index, file_time):
    """takes in an audio file index and file time and returns a book position as (chapter_idx, paragraph_idx, characters_through_paragraph)"""
    total_time = get_total_time(audio_file_start_times, audio_file_index, file_time)
    bookpos = bookpos_from_total_time(book_time_dict, chapter_starts, paragraph_starts, total_time)
    return bookpos


epub_file_path = "alloy/alloy.epub"  # Replace with the path to your EPUB file
epubapp = EPUBReaderApp(epub_file_path)
epubapp.run()

subtitle_file = "alloy/subs/alloy1.srt"
audio_file = "alloy/audio/alloy1.mp3"
player = SubtitlePlayerApp(subtitle_file, audio_file)
player.run()

# BE CAREFUL THIS IS USING THE OLD BOOK READER CODE WHICH DOES NOT STRIP NEWLINES AT CHAPTER START/END
chapter_texts = [epubapp.get_chapter_text(chapter) for chapter in epubapp.book_items_list]
# create booktext as a single string with no newlines
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



start_index = 0
book_time_dict = {}
print("syncing audio and ebooks")
# get lengths of all audio files
audio_files = glob.glob("alloy/audio/*")
audio_file_start_times = []
time_elapsed = 0
for file in audio_files:
    print(file)
    audio_file_start_times.append(time_elapsed)
    playback = Playback(file)
    time_elapsed += playback.duration

print(audio_file_start_times)

subtitle_files = glob.glob("alloy/subs/*")
for i, file in enumerate(subtitle_files):
    print(file)
    subtitles = pysrt.open(file)
    for s in subtitles:
        text = s.text.replace('\n', ' ')
        # Create a SequenceMatcher object
        matcher = difflib.SequenceMatcher(None, booktext, text)

        # Find the best matching substring within the larger text
        match = matcher.find_longest_match(start_index, min(
            start_index+200, len(booktext)), 0, len(text))

        if match.size > 0:
            # Start index of the best match
            start_index = match.a 
            # End index of the best match
            end_index = match.a + match.size

            # print("Start index:", start_index)
            # print("End index:", end_index)
            # print("Best match:", booktext[start_index:end_index])
            book_time_dict[start_index] = get_total_time(audio_file_start_times, i, player.subtitle_time_to_seconds(
                s.start.to_time()))
        else:
            print("No match found.")

        book_index_list = list(book_time_dict.keys())
        is_strictly_increasing = all(i < j for i, j in zip(book_index_list, book_index_list[1:]))
        assert is_strictly_increasing


def get_chapter_paragraph_position(book_index, chapter_starts, paragraph_starts):
    """takes a book index as number of characters through the book and returns 
    (chapter_idx, paragraph_idx, characters_through_paragraph)"""
    # if book_index is negative
    if book_index < 0:
        return 0, 0, 0
    
    chapter_idx = binary_search(chapter_starts, book_index, True) 
    paragraph_idx = binary_search(paragraph_starts[chapter_idx], book_index, True)
    characters_through_paragraph = book_index - paragraph_starts[chapter_idx][paragraph_idx]
    # if book_index is past the last paragraph
    if book_index > paragraph_starts[-1][-1]:
        characters_through_paragraph = 0
    return chapter_idx, paragraph_idx, characters_through_paragraph


def get_book_index(chapter_idx, paragraph_idx, characters_through_paragraph, chapter_starts, paragraph_starts):
    """takes a chapter index, paragraph index, and characters through paragraph and returns 
    the book index as number of characters through the book"""
    book_index = paragraph_starts[chapter_idx][paragraph_idx] + characters_through_paragraph
    return book_index
