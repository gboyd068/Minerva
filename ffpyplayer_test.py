from ffpyplayer.player import MediaPlayer
import time

file = "EoTw/audio/EoTW.mp3"
playback_speed = 1.5
player = MediaPlayer(file, ff_opts={'af': f'atempo={playback_speed}', 'paused':True}) # allowed playback from 0.5 to 100
# does not work without error when immediately seeking !!!
time.sleep(0.1) # this probably depends on hardware speed HELP
player.seek(20) # seeking still goes to original time not the sped up time
player.toggle_pause()
time.sleep(5)
print(player.get_pts())
print(player.get_metadata()["duration"])