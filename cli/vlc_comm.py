import socket
import subprocess
import time
import re
import json
from util import send_until_writable, wait_until_error, path2title, follow
from audio_extract import get_duration
from server_comm import ServerConnection
import os
from termcolor import colored

PORT = 1234

class VLCplayer:  # Class that manages the VLC player instance on the machine.
    player_instance = None
    def __init__(self, port=PORT):
        if(VLCplayer.player_instance is not None):
            self = VLCplayer.player_instance
        else:
            self.port = port
            self.log_file = os.path.abspath('./logs.txt')
            VLCplayer.player_instance = self

    @wait_until_error
    def readState(self):
        """ This reads the JSON state from cache of the video that is currently playing """

        return json.loads(open(os.path.abspath("./cache"), "r").read())

    def launch(self, sub):
        """ Launches a VLC instance """

        bashCommand = "vlc --extraintf=rc --rc-host localhost:%d -vv --file-logging --logfile=%s" % (self.port, self.log_file)
        if sub is not None and os.path.exists(sub):
            bashCommand += " --sub-file='%s'" % (sub)

        print(bashCommand)
        # Start a subprocess to execute the VLC command
        proc = subprocess.Popen(
            bashCommand.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        # proc.stdout.readline()
        # Create a socket connection to the RC interface of VLC that is listening for commands at localhost:1234
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ("localhost", self.port)
        wait_until_error(self.sock.connect, timeout=-1)(self.server_address)
        # Dump any trash data like welcome message that we may recieve from the server after connecting
        # self.sock.recv(1024)
        VLCplayer.player_instance = self

    """ The following functions send a specific command to the VLC instance using the socket connection """

    def play(self):
        message = "play\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def pause(self):
        message = "pause\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def seek(self, position):
        message = f"seek {position}\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def enqueue(self, filePath):
        message = f"enqueue {filePath}\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def faster_playback(self):
        message = "faster\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def slower_playback(self):
        message = "slower\n".encode()
        send_until_writable()(self.sock.sendall, self.sock, message)
        time.sleep(0.5)

    def update(self):
        """ Keeps the VLC instance state updated by parsing the VLC logs that are generated """
        def parse_logs(player, server):
            """ A function that is to be run in a seperate process to parse VLC logs
            and get user events like START,STOP,PLAY,PAUSE,SEEK and accordingly respond
            by sending the data to the server. """
            def on_start(match, state, server):
                file = match[0]
                print("VLC started, data:",file)
                fileFormatted = file.replace('%20', ' ')

                state["path"] = file
                state["title"] = path2title(file)
                state["duration"] = get_duration(file) * 1000
                state["is_playing"] = True
                state["position"] = 0.0
                state["last_updated"] = time.time()
                print(state)

                # server.track_change(videoPath=fileFormatted,state=state)
                # server.track_change(videoPath='abc',state=state)

            def on_stop(match, state, server):
                print("VLC stopped")
                state["is_playing"] = False
                try:
                    del state["duration"]
                except:
                    print("No duration found")
                try:
                    del state["path"]
                    del state["title"]
                except:
                    print("No path found")

                state["position"] = 0.0
                state["last_updated"] = time.time()


            def on_play(match, state, server):
                print("VLC played")
                if not state["is_playing"]:
                    state["is_playing"] = True
                    state["last_updated"] = time.time()
                    # server.send("play", state)


            def on_pause(match, state, server):
                print("VLC paused")
                if state["is_playing"]:
                    state["is_playing"] = False
                    state["position"] = (
                        player.getState()["position"] if player.getState() is not None else 0
                    )
                    state["last_updated"] = time.time()
                    # server.send("pause", state)


            def on_seek(match, state, server):
                match = match[0] or match[1]
                print("VLC seeked , data:", match)
                if "i_pos" in match:
                    # Match is the absolute duratoin
                    match = match.split("=")[1].strip()
                    state["position"] = float(match) / 1000000.0
                    state["last_updated"] = time.time()

                # This is used when seek occurs through the slider
                elif "%" in match:
                    # Match is the percentage of the total duration
                    match = match[:-1]
                    state["position"] = float(match) * float(state["duration"]) / 100000.0
                    state["last_updated"] = time.time()

                # this is for mp4 files
                else:
                    state["position"] = int(match) / 1000
                    state["last_updated"] = time.time()
                # server.send("seek", state)


            def get_regex_match(line):
                for regex in REGEX_DICT:
                    match = re.search(regex, line)
                    if match:
                        return regex, match
                return None, None


            REGEX_DICT = {
                "seek request to (.*)%*$": on_seek,
                "toggling resume$": on_pause,
                "toggling pause$": on_play,
                "main debug: `file.*:///(.*)' successfully opened": on_start,
                "dead input": on_stop,
            }

            state = player.readState()
            if state is None:
                state = {}

            # Continuosly read the VLC logs
            try:
                temp = open(player.log_file,'x')
                temp.close()
            except:
                pass
            logfile = open(player.log_file,'r')
            loglines = follow(logfile)
            for line in loglines:
                print(line)
                regex, match = get_regex_match(line)
                if match is not None:
                    print("MATCH FOUND")
                    try:
                        print("Inside main loop, groups:",match.groups())
                        REGEX_DICT[regex](match.groups(), state, server)
                    except Exception as e:
                        print(match, e) 
            
                # Dump the parsed data into cache
                open(os.path.abspath("./cache"), "w").write(json.dumps(state))
            print("OUTPUT FINISHED!!!")
            logfile.close()
        server = ServerConnection()
        parse_logs(self, server)

    def getState(self):
        """ Interprets the dumped data in cache
        by calculating the live position of the video from the last_updated
        and postition keys in the data. It returns the live state of the video """

        state = self.readState()
        if state is None:
            return
        if "last_updated" in state.keys():
            initial_pos = state["position"]
            extra = (
                time.time() - float(state["last_updated"]) if state["is_playing"] else 0
            )
            final_pos = initial_pos + extra
            state["position"] = final_pos
            state.pop("last_updated")
            return state






