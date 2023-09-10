from flask import Flask, Response, render_template


from camera import Camera
from audio import RATE, CHANNELS, Audio

app = Flask(__name__)


def generate_video(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    # Return the video and audio streaming response
    return Response(generate_video(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')



def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o


def generate_audio(audio):
    bitsPerSample = 16
    wav_header = genHeader(RATE, bitsPerSample, CHANNELS)
    first_run = True
    while True:
        data = audio.get_frame()
        if first_run:
            data = wav_header + data
            first_run = False
        yield data


@app.route('/audio')
def audio():
    return Response(generate_audio(Audio()))


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
