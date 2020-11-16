from django.shortcuts import render
import socketio


sio = socketio.Server(async_mode=None)


@sio.event
def test_event(sid, message):
    print('{} got test message: {}'.format(sid, message))


def index(request):
    return render(request, "index.html")
