import vlc
import time

# Create an instance of VLC MediaPlayer with your file.
player = vlc.MediaPlayer("/home/marceversole/WorkingPipBoy/music/PipBoyStartSound.mp3")

# Start playback.
player.play()

# Wait a bit to allow playback.
time.sleep(10)

# Stop playback.
player.stop()