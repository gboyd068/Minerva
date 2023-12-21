from oscpy.server import OSCThreadServer
from src.playback import Playback
import time


class ServiceManagaer():
    def __init__(self, app_port, service_port):
        self.app_port = app_port
        self.service_port = service_port
        self.osc = OSCThreadServer()
        self.osc.listen(address='localhost', port=service_port, default=True)
        self.playback = None

        # settings
        self.playback_speed = 1.0

        
        # BIND OSC CALLBACKS
        #------------------------
        self.osc.bind(b'/audio', lambda x: print("service received: ", x))
        
        # update settings
        self.osc.bind(b'/update_settings', self.update_settings)
        # loading audio file
        self.osc.bind(b'/load_audio_file', self.load_audio_file)
        # play
        self.osc.bind(b'/play', self.play)
        # pause
        self.osc.bind(b'/pause', self.pause)


    def send_message(self, address, values):
        self.osc.send_message(address, values, 'localhost', self.app_port)

    def update_settings(self, values):
        """
        values = (playback_speed)
        """
        self.playback_speed = float(values[0])
    
    def load_audio_file(self, values):
        """
        values = (filename, start_time=0)
        """
        filename = values[0].decode('utf-8')
        start_time = float(values[1])
        # FUCK THIS IS CALLED FROM audio_thread USUALLY BUT MAY BE CALLED FROM ELSEWHERE!
        self.playback = Playback(filename=filename,
                                  callback=self.audio_callback,
                                  ff_opts={'af': f'atempo={self.playback_speed}',
                                           'ss': start_time, 
                                           'vn': True,
                                           })
        
    def play(self, values):
        if self.playback is not None:
            self.playback.play()

    def pause(self, values):
        if self.playback is not None:
            self.playback.pause()


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
        (current_audio_position: float, is_playing: int)
        """
        if self.playback is not None:
            self.send_message(b'/status', [self.playback.get_pts(), not self.playback.get_pause()])




def service_thread(app_port, service_port):
    service_manager = ServiceManagaer(app_port, service_port)
    while True:
        # need to manage callbacks from playback
        time.sleep(0.1)
        service_manager.status_message()
        