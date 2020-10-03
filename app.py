#!/usr/bin/env python

from importlib import import_module
from os import environ
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='templates')


# import camera driver
if environ.get('CAMERA'):
    Camera = import_module('camera_' + environ['CAMERA']).Camera
else:
    from camera import Camera


@app.get('/', response_class=HTMLResponse)
async def root(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/index.html', response_class=HTMLResponse)
async def index(request: Request) -> Response:
    return RedirectResponse('/')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.get('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return StreamingResponse(gen(Camera()), media_type='multipart/x-mixed-replace; boundary=frame')
