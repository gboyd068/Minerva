from ffpyplayer.player import MediaPlayer
import time

class Playback(MediaPlayer):
    """Wrapper around ffpyplayer's MediaPlayer class that makes it cleaner to use"""
    def __init__(self, **kwargs):
        super().__init__()
        self.pause()
        time.sleep(0.1)
        self.duration = self.get_metadata()["duration"]
    
    def pause(self):
        self.set_pause(True)

    def play(self):
        self.set_pause(False)

    def seek(self, pts):
        super().seek(pts, relative=False, seek_by_bytes=False, accurate=True)
        
def callback_func(a,b):
    print("callback")

if __name__ == "__main__":
    file = r"C:\Users\obion\Documents\projects\audiobookplayer\alloy\audio\alloy9.mp3"
    playback_speed = 1
    player = Playback(filename=file, thread_lib="python", callback=callback_func, ff_opts={'ss':500., 't':500., 'af': f'atempo={playback_speed}'}) # allowed playback from 0.5 to 100
    playing = not player.get_pause()
    print(playing)
    print(player.duration)
    print(player.get_pts())
    player.play()
    time.sleep(2)
    print(player.get_pts())