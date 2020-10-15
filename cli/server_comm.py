import socketio
import time
import psutil

from util import path2title
from termcolor import colored

SERVER_ADDR = "localhost"
ARGS = {}


# this is used internally by ServerConnection
class VLC_signals(socketio.ClientNamespace):
    def bind(self):
        """ Binds the player instance to this class instance. """

        from vlc_comm import player

        self.player = player

    """ Functions with name like on_event are executed when a signal named 'event' is recieved from the server. """

    def on_connect(self):
        print("connected")

    def on_userId(self, data):
        print("userId is ", colored(data, "blue"))

    def on_disconnect(self):
        print(
            colored("\nDisconnected...", "red")
            + colored("\nExiting Now...Goodbye!", "green")
        )

    def on_play(self, *args, **kwargs):
        state = args[0]
        print(f"[{colored('$','blue')}] Play signal recieved")
        self.player.play()

    def on_pause(self, *args, **kwargs):
        state = args[0]
        print(f"[{colored('$','blue')}] Pause signal recieved")
        self.player.pause()

    def on_seek(self, *args, **kwargs):
        state = args[0]
        seek_time = int(time.time() - state["last_updated"] + state["position"])
        print(
            f"[{colored('$','blue')}] Seek signal recieved ==> seeking to {colored(seek_time,'yellow')}"
        )
        self.player.seek(seek_time)

    def on_createRoom(self, *args, **kwargs):
        self.roomId = args[0]["roomId"]

        url = "http://%s:5000/client/stream/?roomId=%s"
        if ARGS["web"]:
            url = url % (SERVER_ADDR, self.roomId)
        else:
            url = url % (ARGS["localIP"], self.roomId)
        from util import print_url

        print_url(url)
        if ARGS["qr"]:
            from util import print_qr

            print(f"\n[{colored('$','blue')}] Or scan the QR code given below")
            print_qr(url)


class ServerConnection:
    # Class that handles all connections to the server
    def __init__(self):
        self.sio = socketio.Client()
        self.sio.connect("http://localhost:5000")
        self.tracks = {}
    def send(self, signal, data):
        """ Used to send data to the server with a corresponding signal"""
        self.sio.emit(signal, data)

    def start_listening(self):
        """ Establish connection to the server and start listening for signals from the server """

        self.signals = VLC_signals("/")
        self.signals.bind()
        self.sio.register_namespace(self.signals)

    def track_change(self,videoPath,state):
        print(f"[{colored('#','yellow')}] Changing track to ", colored(path2title(videoPath),'green') )
        self.send('changeTrack',{
            self.tracks[videoPath][0] : self.tracks[videoPath][1],
            "state": state
        })

    def add_track(self, videoPath):
        self.send(
            "addTrack",
            {
                "title": path2title(videoPath),
                self.tracks[videoPath][0]: self.tracks[videoPath][1],
            },
        )

    def create_room(self):
        self.send('createRoom',{
            "onlyHost": ARGS["onlyHost"]
        })

    def upload(self, videoPath ,audioPath):
        """ Uploads audio file to the webserver """
        print(f"[{colored('+','green')}] Uploading {colored(path2title(audioPath),'green')} to server ...")
        import requests

        url = f"http://{SERVER_ADDR}:5000/api/upload/"
        files = {"file": (path2title(videoPath), open(audioPath, "rb"), "audio/ogg")}
        r = requests.post(url=url, files=files, data={"title": path2title(videoPath)})

        self.tracks[videoPath]= ("trackId" ,r.json()['trackId'])
        print(
            f"[{colored('+','green')}] Upload complete for file {colored(path2title(audioPath),'green')}")

    def addAudioPath(self, videoPath, audioPath):
        self.tracks[videoPath] = ("audioPath", audioPath)


def set_vars(args):
    ARGS["web"] = args.web
    ARGS["qr"] = args.qr
    ARGS["onlyHost"] = args.onlyHost
    ARGS["localIP"] = args.localIP
