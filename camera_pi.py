import io
import time
import picamera
from base_camera import BaseCamera


class Camera(BaseCamera):
    @staticmethod
    def frames():
        with picamera.PiCamera(resolution='1640x1232', framerate=10) as camera:
            # let camera warm up
            time.sleep(2)

            camera.vflip = True
            camera.hflip = True

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, 
                                                format='jpeg', 
                                                use_video_port=True):
                # return current frame
                stream.seek(0)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
