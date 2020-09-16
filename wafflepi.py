import io
import logging
import socketserver
import picamera
from threading import Condition
from http import server

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body style="margin: 0">
<div id="waffleImage" onclick="toggleFullScreen()"></div>

<style>
#waffleImage {
    height: 100%;
    width: 100%;
    background: url('stream.mjpg');
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain; 
}

#waffleImage:fullscreen {
    background-position: bottom;
    background-size: cover;
}
</style>

<script>
var element = document.getElementById('waffleImage');
function toggleFullScreen() {
    try {
        if (!document.fullscreenElement) {
            element.requestFullscreen();

        } else if (document.exitFullscreen) {
            document.exitFullscreen(); 
        }
    } catch(e) {
        window.alert('sorry unable to go to fullscreen! ' + e.message);
    }
}
</script>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

output = StreamingOutput()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class WaffleServer(object):
    def __init__(self):
        self.camera = picamera.PiCamera(resolution='1640x1232', framerate=10)
        # self.camera.exposure_compensation = 6
        # self.camera.exposure_mode = 'off'
        self.camera.vflip = True
        self.camera.hflip = True
        self.camera.start_recording(output, format='mjpeg')

    def stop(self):
        self.camera.stop_recording()
        self.camera.close()

    def start(self, port):
        try:
            address = ('', port)
            server = StreamingServer(address, StreamingHandler)
            server.serve_forever()
        finally:
            self.stop()

if __name__ == "__main__":
    import sys
    server = WaffleServer()
    server.start(80)