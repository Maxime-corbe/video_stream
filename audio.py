import time
from _thread import get_ident
import threading

import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024


class AudioEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the audio thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseAudio(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = AudioEvent()

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseAudio.thread is None:
            BaseAudio.last_access = time.time()

            # start background frame thread
            BaseAudio.thread = threading.Thread(target=self._thread)
            BaseAudio.thread.start()

            # wait until first frame is available
            BaseAudio.event.wait()

    def get_frame(self):
        """Return the current camera frame."""
        BaseAudio.last_access = time.time()

        # wait for a signal from the camera thread
        BaseAudio.event.wait()
        BaseAudio.event.clear()

        return BaseAudio.frame

    def frames(self):
        """"Generator that returns frames from the mic."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def _thread(cls):
        """audio background thread."""
        print('Starting audio thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseAudio.frame = frame
            BaseAudio.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - BaseAudio.last_access > 10:
                cls.stream.close()
                cls.audio.terminate()
                frames_iterator.close()
                print('Stopping audio thread due to inactivity.')
                break
        BaseAudio.thread = None


class Audio(BaseAudio):
    def frames(self):
        self.audio = pyaudio.PyAudio()
        while True:
            try:
                self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                              rate=RATE, input=True, input_device_index=1,
                                              frames_per_buffer=CHUNK)
            except OSError:
                time.sleep(2)
            else:
                break
        print("recording...")
        # frames = []
        while True:
            yield self.stream.read(CHUNK, exception_on_overflow=False)
