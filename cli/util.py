import time
import os
import pyqrcode
import subprocess
import re
from audio_extract import convert2mkv, extract
from termcolor import colored
import threading
import filetype
import itertools
import sys
import socket
import colorama


def print_url(url):
    """ Makes a txt file with the URL that is received from the server for the GUI app. """

    print(f"\n[{colored('$','blue')}] Please visit {colored(url,'cyan')}")
    f = open("invite_link.txt", "w")
    f.write(url)
    f.close()


def generate_qr(url):
    image = pyqrcode.create(url)
    image.png('invite_link.png', scale=10)

def print_qr():
    """ Prints a QR code using the URL that we received from the server. """
    subprocess.Popen('start invite_link.png'.split())


def get_videos(path, clear_files):

    if os.path.isfile(path):
        kind = filetype.guess(path)
        if kind and "video" in kind.mime:
            if kind.mime == "video/x-matroska":
                return [path]
            else:
                try:
                    print(
                        f"[{colored('+','green')}] Converting {path2title(path)} to MKV",
                        end="",
                    )
                    from audio_extract import convert2mkv

                    new_file = convert2mkv(path)
                    clear_files.append(new_file)
                    return [new_file]
                except Exception as e:
                    print(e)
                    return []
        return []
    if os.path.isdir(path):
        ans = []
        for file in os.listdir(path):
            ans.extend(get_videos(path + "/" + file, clear_files))
        return ans


def path2title(path):
    return path.split("/")[-1:][0]



def getLocalIP():
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    
    try:
        sock.connect(('1.1.1.1',1000))
        return sock.getsockname()[0]
    except:
        return input(f"[{colored('$','red')}] Unable to find IP address. Enter your local IP address: ")
    
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def spawn_server(args):
    os.system('taskkill /IM "CAV_server.exe" /F')
    time.sleep(1)

    proc = subprocess.Popen(resource_path('CAV_server.exe'),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # for line in iter(proc.stdout.readline, ""):
    #     print("server: "+line.decode())
    #     if b"npm ERR!" in line:
    #         print(colored(line, "red"))
    #         print(
    #             f"[{colored('-','red')}] An error has occured while starting the server\nRestarting the server"
    #         )
    #         os.system('taskkill /IM "CAV_server.exe" /F')
    #         os.system(f"taskkill /F /PID {os.getpid()}")
    #     if b"Press CTRL-C to stop" in line:
    #         pass
    # SERVER_PATH = os.path.abspath("../../CommonAudioVideoServer/")

    # if not os.path.exists(SERVER_PATH):
    #     print(
    #         f"[{colored('-','red')}] Invalid Server Path, Try {colored('reinstalling','red')} the package"
    #     )
    #     sys.exit(-1)

    # if not os.path.exists(SERVER_PATH + "\\node_modules"):
    #     print(f"[{colored('+','green')}] Configuring the server ..")
    #     anim = Animation()
    #     subprocess.Popen(
    #         "npm install".split(),
    #         stdout=subprocess.DEVNULL,
    #         stderr=subprocess.DEVNULL,
    #         cwd=SERVER_PATH,
    #         shell=True,
    #     ).wait()
    #     anim.complete()
    #     print(f"[{colored('+','green')}] Server configuration complete ..")

    # if args.rebuild:
    #     print(f"[{colored('+','green')}] Building server ..")
    #     anim = Animation()
    #     subprocess.Popen(
    #         "npm run compile".split(),
    #         stdout=subprocess.DEVNULL,
    #         stderr=subprocess.DEVNULL,
    #         cwd=SERVER_PATH,
    #         shell=True,
    #     ).wait()
    #     anim.complete()
    #     print(f"[{colored('+','green')}] Server build successfull ..")

    # print(f"[{colored('+','green')}] Initializing Server ..")
    # anim = Animation()
    # proc = subprocess.Popen(
    #     "npm start".split(),
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT,
    #     cwd=SERVER_PATH,
    #     shell=True,
    # )
    # for line in iter(proc.stdout.readline, ""):
    #     if b"npm ERR!" in line:
    #         print(colored(line, "red"))
    #         print(
    #             f"[{colored('-','red')}] An error has occured while starting the server\nRestarting the server"
    #         )
    #         os.system('taskkill /IM "node.exe" /F')
    #         os.system(f"taskkill /F /PID {os.getpid()}")
    #     if b"Press CTRL-C to stop" in line:
    #         anim.complete()
    #         return proc




class Animation:
    def __init__(self):
        self.done = False
        t = threading.Thread(target=self.animate)
        t.start()

    def animate(self):
        sys.stdout.write(" -- loading |")
        for c in itertools.cycle(["|", "/", "-", "\\"]):
            time.sleep(0.1)
            if self.done:
                break
            sys.stdout.write("\b" + c)
            sys.stdout.flush()

    def complete(self):
        self.done = True
        sys.stdout.write("\b..Done!\n")
