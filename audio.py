import pyaudio
from stream_base import BaseStream

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 1024


class Audio(BaseStream):
    @staticmethod
    def frames():
        audio1 = pyaudio.PyAudio()
        stream = audio1.open(format=FORMAT, channels=CHANNELS,
                             rate=RATE, input=True, input_device_index=1,
                             frames_per_buffer=CHUNK)
        print("recording...")
        # frames = []
        while True:
            yield stream.read(CHUNK, exception_on_overflow=False)
