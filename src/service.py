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
        
        # bind osc callbacks
        self.osc.bind(b'/audio', lambda x: print("service received: ", x))


    def send_message(self, address, values):
        self.osc.send_message(address, values, 'localhost', self.app_port)


def service_thread(app_port, service_port):
    service_manager = ServiceManagaer(app_port, service_port)
    t0 = time.time()
    while True:
        time.sleep(1)
        t = time.time()
        is_playing = True
        service_manager.send_message(b'/status', [is_playing, t-t0])
        