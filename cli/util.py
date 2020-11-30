import time
import os
from select import select
import pyqrcode
import subprocess
import re
# from magic import Magic
import filetype
from audio_extract import convert2mkv
from termcolor import colored
import threading
import itertools
import sys
import socket


def wait_until_error(f, timeout=0.5):
    """ Wait for timeout seconds until the function stops throwing any errors. """

    def inner(*args, **kwargs):
        st = time.perf_counter()
        while time.perf_counter() - st < timeout or timeout < 0:
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if e or not e:
                    continue

    return inner


def send_until_writable(timeout=0.5):
    """ This will send a message to the socket only when it is writable and wait for timeout seconds
    for the socket to become writable, if the socket was busy. """

    def inner(f, socket, message):
        st = time.perf_counter()
        while time.perf_counter() - st < timeout:
            if check_writable(socket):
                return f(message)

    return inner


def check_writable(socket):
    """ Checks whether the socket is writable """

    _, writable, _ = select([], [socket], [], 60)
    return writable == [socket]


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
    subprocess.Popen('xdg-open invite_link.png'.split())

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
