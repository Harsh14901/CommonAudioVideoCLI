import argparse
import sys
import signal
import time
import os
import subprocess
from multiprocessing import Process, Pool
from multiprocessing.managers import BaseManager

from termcolor import colored
import colorama

from server_comm import ServerConnection
from audio_extract import convert_async
from util import *


TO_CLEAR = ["cache", "invite_link.txt", "invite_link.svg"]


def parse():
    parser = argparse.ArgumentParser(
        description="Route audio of a video file through a local server."
    )
    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        "-f",
        "--file",
        required=True,
        dest="f",
        help="Path to video files or directory containing video files",
        type=str,
        action="append",
    )
    parser.add_argument(
        "--qr", help="Show qr code with the link", dest="qr", action="store_true"
    )
    parser.add_argument(
        "--control",
        help="only host can control play/pause signals",
        dest="onlyHost",
        action="store_true",
    )
    parser.add_argument(
        "--force-rebuild",
        help="Force rebuild of the local server",
        dest="rebuild",
        action="store_true",
    )
    parser.add_argument(
        "--audio-quality",
        dest="q",
        help="Audio quality to sync from",
        choices=["low", "medium", "good", "high"],
        type=str,
        default="medium",
    )

    group.add_argument(
        "--web",
        help="Force routing through a web server",
        dest="web",
        action="store_true",
    )
    args = parser.parse_args()
    args.localIP = getLocalIP()
    videos = []
    for i in range(len(args.f)):
        args.f[i] = os.path.abspath(args.f[i])
        videos.extend(get_videos(args.f[i], TO_CLEAR))
    args.f = videos
    return args


def initialize(videos, server, first=False):
    audio = convert_async(videos, args)

    for video in videos:

        if args.web:
            server.upload(video, video[:-3] + "ogg")
        else:
            server.addAudioPath(video, video[:-3] + "ogg")
        if(first):
            server.create_room()
        server.add_track(video)


def exitHandler(*args, **kwargs):
    os.system('taskkill /IM "node.exe" /F')
    for file in TO_CLEAR:
        if os.path.exists(os.path.abspath(file)):
            try:
                os.remove(file)
            except:
                pass

    os.system(f"taskkill /F /PID {os.getpid()}")

if __name__ == "__main__":

    # signal.signal(signal.SIGINT, exitHandler)
    colorama.init()
    args = parse()

    # spawn_server(args)

    server = ServerConnection(args)

    initialize([args.f[0]], server=server, first=True)
    if len(args.f) > 1:
        initialize(args.f[1:],server)

    print("\n" + colored("#" * 70, "green") + "\n")
    while(True):
        time.sleep(1)