import time
import os
from select import select
import pyqrcode
import subprocess
import re
from magic import Magic
from audio_extract import convert2mkv
from termcolor import colored
import threading
import itertools
import sys


def wait_until_error(f, timeout=0.5):
    """ Wait for timeout seconds until the function stops throwing any errors. """

    def inner(*args, **kwargs):
        st = time.perf_counter()
        while time.perf_counter() - st < timeout or timeout < 0:
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # print(e)
                pass

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


def print_qr(url):
    """ Prints a QR code using the URL that we received from the server. """

    image = pyqrcode.create(url)
    image.svg("invite_link.svg", scale=1)
    print(image.terminal(quiet_zone=1))


def get_videos(path, clear_files):

    if os.path.isfile(path):
        mime = Magic(magic_file="C:\Windows\System32\magic.mgc" ,mime=True).from_file(path)
        if "video" in mime:
            if mime == "video/x-matroska":
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


def get_interface():
    arp_details = subprocess.Popen(
        "arp -a".split(), stdout=subprocess.PIPE
    ).communicate()
    arp_details = arp_details[0].decode().split("\n")[:-1]

    intf = None
    for detail in arp_details:
        match = re.search("on (.*)$", detail)
        if match is not None:
            new_intf = match.groups()[0]
            if intf is not None and intf != new_intf:
                return input(f"[{colored('+','green')}] Enter the interface to use: ")
            intf = new_intf
    if intf is None:
        return input(f"[{colored('+','green')}] Enter the interface to use: ")

    return intf

def follow(thefile):
    thefile.seek(0,2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.01)
            continue
        yield line

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
