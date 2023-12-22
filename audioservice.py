from oscpy.server import OSCThreadServer
# from src.playback import Playback
import time
from functools import partial
from kivy.utils import platform
if platform == 'android':
    from jnius import autoclass
    PythonService = autoclass('org.kivy.android.PythonService')
    MediaPlayer = autoclass('android.media.MediaPlayer')
    PlaybackParams = autoclass('android.media.PlaybackParams')
    PythonService.mService.setAutoRestartService(True)

class ServiceManagaer():
    def __init__(self, app_port, service_port):
        self.app_port = app_port
        self.service_port = service_port
        self.osc = OSCThreadServer()
        self.osc.listen(address='localhost', port=service_port, default=True)
        self.playback = MediaPlayer()
        self.playback_params = PlaybackParams()
        self.start_time = None
        self.current_audio_idx = -1
        self.filenames = None

        # settings
        self.playback_speed = 1.0
        self.playback_params.setSpeed(self.playback_speed)

        
        # BIND OSC CALLBACKS
        #------------------------
        self.osc.bind(b'/test', lambda x: print("service received: ", x))
        
        # update settings
        self.osc.bind(b'/update_settings', self.update_settings)
        # loading audio file
        self.osc.bind(b'/load_audio_file', partial(load_audio_file,self))
        # play
        self.osc.bind(b'/play', self.play)
        # pause
        self.osc.bind(b'/pause', self.pause)
        # seek
        self.osc.bind(b'/seek', self.seek)
        # update filenames
        self.osc.bind(b'/update_filenames', self.update_filenames)



    # NEED TO SEND OVER ALL THE FILENAMES, WHAT HAPPENS IF WE GO TO NEXT FILE WHILE MINIMIZED
    def send_message(self, address, values):
        self.osc.send_message(address, values, 'localhost', self.app_port)

    def update_filenames(self, *values):
        """
        values is tuple of filenames as bytestrings
        """
        self.filenames = [filename.decode('utf-8') for filename in values]

    def update_settings(self, *values):
        """
        values = (playback_speed)
        """
        print("service settings update", values)
        self.playback_speed = float(values[0])
        if 0 < self.playback_speed < 3:
            self.playback_params.setSpeed(self.playback_speed)
            is_playing = self.playback.isPlaying()
            self.playback.setPlaybackParams(self.playback_params) # changing to non-zero speed causes play
            if not is_playing:
                self.playback.pause()

        
    def play(self, *values):
        print("play")
        if self.playback.getDuration() != -1:
            self.playback.start()

    def pause(self, *values):
        print("pause")
        if self.playback.getDuration() != -1:
            self.playback.pause()
    
    def seek(self, *values):
        print("seeking")
        if self.playback.getDuration() != -1:
            self.playback.seekTo(int(values[0]*1000))


    def audio_callback(self, selector, value):
        if selector == "read:exit":
            pass
            # set slider value
        if selector == "eof":
            print("eof")
            # deal with end of audio segment
            
            # deal with actual end of file

    def status_message(self):
        """
        send osc message to app with current status
        (current_audio_idx:int, current_audio_position: float, is_playing: int, duration: float)
        """
        if self.playback.getDuration() != -1:
            current_position = self.playback.getCurrentPosition()/1000
            self.send_message(b'/status', [self.current_audio_idx, current_position, self.playback.isPlaying(), self.playback.getDuration()/1000])


# I have no idea why the others work fine as methods but this one doesnt
def load_audio_file(service_manager, *values):
    """
    values = (audio_file_idx, start_time=0, is_playing)
    """
    filename = service_manager.filenames[int(values[0])]
    start_time = float(values[1])
    is_playing = bool(values[2])
    print(filename, start_time)
    service_manager.start_time  = start_time
    service_manager.playback.reset()
    service_manager.playback.setDataSource(filename)
    service_manager.playback.setPlaybackParams(service_manager.playback_params)
    service_manager.playback.prepare()
    service_manager.playback.seekTo(int(start_time*1000))
    # service_manager.playback = Playback(filename=filename,
    #                             callback=service_manager.audio_callback,
    #                             ff_opts={'af': f'atempo={service_manager.playback_speed}',
    #                                     'ss': start_time, 
    #                                     'vn': True,
    #                                     })
    if is_playing:
        service_manager.play()


def service_thread(app_port, service_port):
    print("STARTING SERVICE")
    service_manager = ServiceManagaer(app_port, service_port)
    while True:
        # need to manage callbacks from playback
        time.sleep(0.1)
        service_manager.status_message()
        

service_thread(8000, 8001)