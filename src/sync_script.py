import difflib
import os
import glob
import json
import pysrt
import time
from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp
from kivy.core.window import Window
from src.playback import Playback

class SyncScript():
    def __init__(self, audio_player, reader_window):
        self.audio_player = audio_player
        self.reader_window = reader_window
        self.slider = None
        self.book_path = None # potentially load book that was last used in app
        self.book_time_dict = {}
        self.chapter_starts = []
        self.paragraph_starts = []
        self.audio_file_start_times = []
        self.total_duration = None
        self.end_page_bookpos = None
        self.sync_data_path = None
        self.auto_page_turn_enabled = not "0"==MDApp.get_running_app().config.get("General", "auto_page_turn")


    def update_end_page_bookpos(self, bookpos):
        self.end_page_bookpos = bookpos
    
    def sync_to_audio_position(self):
        audio_file_idx = self.audio_player.current_audio_idx
        audio_position = self.audio_player.current_audio_position
        bookpos = self.bookpos_from_file_time(audio_file_idx, audio_position)
        self.reader_window.current_item_index = bookpos[0]
        self.reader_window.chapter_text = self.reader_window.get_chapter_text(self.reader_window.book_items_list[bookpos[0]])
        self.reader_window.paragraph_within_chapter = bookpos[1]
        self.reader_window.start_page_paragraph_pos = 0
        self.reader_window.display_page()

    def sync_to_text_position(self):
        self.audio_player.enable_status_update = False
        bookpos = (self.reader_window.current_item_index, self.reader_window.paragraph_within_chapter, self.reader_window.start_page_paragraph_pos)
        audio_file_idx, audio_position = self.file_time_from_bookpos(bookpos)
        self.audio_player.go_to_audio_file_position(audio_file_idx, audio_position, sync=False)
        self.audio_player.enable_status_update = True

    def load_sync_data(self):
        """loads sync data from a json file if it exists, otherwise returns False"""
        user_data_dir = MDApp.get_running_app().user_data_dir
        book_dir_name = os.path.basename(self.book_path)
        book_data_dir = os.path.join(user_data_dir, book_dir_name)
        self.sync_data_path = os.path.join(book_data_dir, "sync_data.json")
        try:
            if not os.path.exists(book_data_dir):
                os.makedirs(book_data_dir)
            with open(self.sync_data_path) as f:
                sync_data = json.load(f)
            # check the sync_data is valid
            assert "chapter_starts" in sync_data
            assert "paragraph_starts" in sync_data
            assert "audio_file_start_times" in sync_data
            assert "total_duration" in sync_data
            assert "book_time_dict" in sync_data
        except (FileNotFoundError, AssertionError):
            return False
        return sync_data


    def _index_ebook(self):
        """generates lists of the starts of chapters and paragraphs in the book in terms of characters through the book"""
        chapter_texts = [self.reader_window.get_chapter_text(chapter) for chapter in self.reader_window.book_items_list]
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
        return booktext, chapter_starts, paragraph_starts
    

    def _index_audiobook(self):
        # get lengths of all audio files
        audio_files = glob.glob(os.path.join(self.book_path, "audio", "*.mp3"))
        audio_files.sort()
        audio_file_start_times = []
        time_elapsed = 0
        for file in audio_files:
            audio_file_start_times.append(time_elapsed)
            playback = Playback(filename=file)
            time_elapsed += playback.duration
        total_duration = time_elapsed
        return audio_file_start_times, total_duration




    def _generate_sync_data(self, dialog):
        sync_data = {}
        # get chapter and paragraph starts
        booktext, self.chapter_starts, self.paragraph_starts = self._index_ebook()
        sync_data["chapter_starts"] = self.chapter_starts
        sync_data["paragraph_starts"] = self.paragraph_starts
        # get audio file start times
        self.audio_file_start_times, self.total_duration = self._index_audiobook()
        sync_data["audio_file_start_times"] = self.audio_file_start_times
        sync_data["total_duration"] = self.total_duration

        # get book time dict
        start_index = 0
        book_time_dict = {}

        subtitle_files = glob.glob(os.path.join(self.book_path, "subs", "*.srt"))
        subtitle_files.sort()
        print(subtitle_files)
        step_size = 200
        for i, file in enumerate(subtitle_files):
            print("syncing", file)
            subtitles = pysrt.open(file)
            for sidx, s in enumerate(subtitles):
                # move on to next subtitle if that subtitle isn't in the book
                if step_size > len(booktext)//10:
                    continue
                text = s.text.replace('\n', ' ')
                # Create a SequenceMatcher object
                matcher = difflib.SequenceMatcher(None, booktext, text)
                sub_length = len(text)
                # Find the best matching substring within the larger text
                match = matcher.find_longest_match(start_index, min(
                    start_index+step_size, len(booktext)), 0, len(text))
                # do a reverse comparison from that result
                
                # get text from book that matches the same region of characters
                book_match_region = booktext[match.a-match.b:match.a-match.b+sub_length]
                # compare with ratio
                ratio = difflib.SequenceMatcher(None, text, book_match_region).ratio()

                if ratio > 0.75: # reasonable match is found
                    step_size = 200
                    # Start index of the best match
                    start_index = match.a - match.b
                    # End index of the best match
                    end_index = match.a + match.size
                    book_time_dict[start_index] = self.get_total_time(i, self.audio_player.subtitle_time_to_seconds(
                        s.start))
                else:
                    # print("No match found.")
                    step_size += 200

                book_index_list = list(book_time_dict.keys())
                is_strictly_increasing = all(i < j for i, j in zip(book_index_list, book_index_list[1:]))
                # assert is_strictly_increasing

        sync_data["book_time_dict"] = book_time_dict

        with open(self.sync_data_path, 'w+') as f:
            json.dump(sync_data, f)
        self._finish_load_book(sync_data)
        dialog.dismiss()




    def load_book(self, book_path):
        """loads a book from a path, returns metadata about the book for the library screen"""
        # if its a valid path then load it
        self.book_path = book_path
        # load ebook
        self.reader_window.load_epub(  glob.glob(os.path.join(self.book_path, "*.epub"))[0] )
        # load audiobook
        self.audio_player.audio_path = os.path.join(self.book_path, "audio")
        self.audio_player.load_audio_path(self.audio_player.audio_path)
    
        sync_data = self.load_sync_data()
        # sync if not already synced
        if not sync_data:
            # make a popup
            dialog = MDDialog(text="Syncing...")
            dialog.open()
            Clock.schedule_once(lambda dt: self._generate_sync_data(dialog))
        else:
            Clock.schedule_once(lambda dt: self._finish_load_book(sync_data))


    def _finish_load_book(self, sync_data):
        # convert dict to right formats
        self.book_time_dict = sync_data["book_time_dict"]
        self.chapter_starts = sync_data["chapter_starts"]
        self.paragraph_starts = sync_data["paragraph_starts"]
        self.audio_file_start_times = sync_data["audio_file_start_times"]
        self.total_duration = sync_data["total_duration"]
        self.book_time_dict = {int(k):v for k,v in self.book_time_dict.items()}
        # go to the correct saved position in the book/audiobook
        self.audio_player.load_last_played_timestamp()
        self.audio_player.enable_status_update = True


    def binary_search(self, arr, x, return_idx=False):
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

    def total_time_from_bookpos(self, bookpos):
        """takes in a book position as (chapter_idx, paragraph_idx, characters_through_paragraph) and returns the total time"""
        book_index = self.get_book_index(*bookpos)
        book_index_list = list(self.book_time_dict.keys())
        nearest_book_index = self.binary_search(book_index_list, book_index)
        return self.book_time_dict[nearest_book_index]


    def bookpos_from_total_time(self, total_time):
        """takes in a total time and returns a book position as (chapter_idx, paragraph_idx, characters_through_paragraph)"""
        nearest_time = self.binary_search(list(self.book_time_dict.values()), total_time)
        index = list(self.book_time_dict.values()).index(nearest_time)
        book_index = list(self.book_time_dict.keys())[index]
        bookpos = self.get_chapter_paragraph_position(book_index)
        return bookpos

    def get_total_time(self, audio_file_index, file_time):
        """takes the current audio file index and the time in that file and returns the total time elapsed"""
        total_time = self.audio_file_start_times[audio_file_index] + file_time
        return total_time

    def get_audio_file_index_and_file_time(self, total_time):
        """takes the total time elapsed and returns the audio file index"""
        audio_file_index = self.binary_search(self.audio_file_start_times, total_time, True)
        file_time = total_time - self.audio_file_start_times[audio_file_index]
        return audio_file_index, file_time


    def file_time_from_bookpos(self, bookpos):
        """takes in a book position as (chapter_idx, paragraph_idx, characters_through_paragraph) and returns audio file and file time"""
        total_time = self.total_time_from_bookpos(bookpos)
        audio_file_index, file_time = self.get_audio_file_index_and_file_time(total_time)
        return audio_file_index, file_time

    def bookpos_from_file_time(self, audio_file_index, file_time):
        """takes in an audio file index and file time and returns a book position as (chapter_idx, paragraph_idx, characters_through_paragraph)"""
        total_time = self.get_total_time(audio_file_index, file_time)
        bookpos = self.bookpos_from_total_time(total_time)
        return bookpos

    def get_chapter_paragraph_position(self, book_index):
        """takes a book index as number of characters through the book and returns 
        (chapter_idx, paragraph_idx, characters_through_paragraph)"""
        # if book_index is negative
        if book_index < 0:
            return 0, 0, 0
        
        chapter_idx = self.binary_search(self.chapter_starts, book_index, True) 
        paragraph_idx = self.binary_search(self.paragraph_starts[chapter_idx], book_index, True)
        characters_through_paragraph = book_index - self.paragraph_starts[chapter_idx][paragraph_idx]
        # if book_index is past the last paragraph
        if book_index > self.paragraph_starts[-1][-1]:
            characters_through_paragraph = 0
        return chapter_idx, paragraph_idx, characters_through_paragraph


    def get_book_index(self, chapter_idx, paragraph_idx, characters_through_paragraph):
        """takes a chapter index, paragraph index, and characters through paragraph and returns 
        the book index as number of characters through the book"""
        book_index = self.paragraph_starts[chapter_idx][paragraph_idx] + characters_through_paragraph
        return book_index