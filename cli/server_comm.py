import socketio
import time
import psutil
import os
from util import path2title
from termcolor import colored

SERVER_ADDR = "localhost"
# ARGS = {}


# this is used internally by ServerConnection
class VLC_signals(socketio.ClientNamespace):

    def __init__(self, *args , **kwargs):
        self.ARGS = kwargs['params']
        del kwargs['params']
        super().__init__(*args ,**kwargs)

    def on_createRoom(self, *args, **kwargs):
        self.roomId = args[0]["roomId"]

        url = "http://%s:5000/client/stream/?roomId=%s"
        if self.ARGS["web"]:
            url = url % (SERVER_ADDR, self.roomId)
        else:
            url = url % (self.ARGS['localIP'], self.roomId)
        
        os.system(f"start \"\" {url.replace('client','host')}")
        from util import print_url

        print_url(url)
        if self.ARGS["qr"]:
            from util import print_qr,generate_qr

            print(f"\n[{colored('$','blue')}] Or scan the QR code given below")
            generate_qr(url)
            # print_qr()


class ServerConnection:
    # Class that handles all connections to the server
    server_instance = None
    def __init__(self, args=None):
        if(ServerConnection.server_instance is not None):
            self = ServerConnection.server_instance
        else:
            try:
                self.ARGS = {}
                self.ARGS['web'] = args.web
                self.ARGS['qr'] = args.qr
                self.ARGS['onlyHost'] = args.onlyHost
                self.ARGS['localIP'] = args.localIP
            except:
                pass
            
            self.sio = socketio.Client()
            self.sio.connect(f"http://{SERVER_ADDR}:5000")
            self.tracks = {}
            
            self.start_listening()
            ServerConnection.server_instance = self


    def send(self, signal, data):
        """ Used to send data to the server with a corresponding signal"""
        self.sio.emit(signal, data)

    def start_listening(self):
        """ Establish connection to the server and start listening for signals from the server """

        self.signals = VLC_signals("/",params = self.ARGS)
        self.sio.register_namespace(self.signals)

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
            "onlyHost": self.ARGS["onlyHost"]
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

