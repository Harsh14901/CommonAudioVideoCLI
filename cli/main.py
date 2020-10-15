import argparse
import sys
import signal
import time
import os
import subprocess
from multiprocessing import Process, Pool
from multiprocessing.managers import BaseManager
from itertools import product
from termcolor import colored

from server_comm import ServerConnection, set_vars
from vlc_comm import player
from util import get_videos, path2title, Animation, getLocalIP
from audio_extract import extract

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

    videos = []

    for i in range(len(args.f)):
        args.f[i] = os.path.abspath(args.f[i])
        videos.extend(get_videos(args.f[i], TO_CLEAR))
    args.f = videos
    return args


def convert_async(paths):
    """ Converts video files to audio files asynchronously
    using a pool of processes """
    pool = Pool()
    files = []
    st = time.perf_counter()
    print(f"[{colored('+','green')}] Extraction of audio started ...")
    p = pool.starmap_async(extract, product(paths, [args.q]), callback=files.extend)

    p.wait()
    print(
        f"[{colored('+','green')}] Completed extraction of {colored(len(paths),'yellow')} file(s) in {colored(time.perf_counter()-st,'yellow')} seconds"
    )
    return files


def exitHandler(*args, **kwargs):
    os.system("killall node 2> /dev/null")
    os.system("killall npm 2> /dev/null")
    for file in TO_CLEAR:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

    sys.exit(0)


def spawn_server():
    SERVER_PATH = "../../CommonAudioVideoServer/"

    if not os.path.exists(SERVER_PATH):
        print(
            f"[{colored('-','red')}] Invalid Server Path, Try {colored(reinstalling,'red')} the package"
        )
        sys.exit(-1)

    if not os.path.exists(SERVER_PATH + "node_modules"):
        print(f"[{colored('+','green')}] Configuring the server ..")
        anim = Animation()
        subprocess.Popen(
            "npm install".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd() + "/" + SERVER_PATH,
        ).wait()
        anim.complete()
        print(f"[{colored('+','green')}] Server configuration complete ..")

    if args.rebuild:
        print(f"[{colored('+','green')}] Building server ..")
        anim = Animation()
        subprocess.Popen(
            "npm run compile".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd() + "/" + SERVER_PATH,
        ).wait()
        anim.complete()
        print(f"[{colored('+','green')}] Server build successfull ..")

    print(f"[{colored('+','green')}] Initializing Server ..")
    anim = Animation()
    proc = subprocess.Popen(
        "npm start".split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=os.getcwd() + "/" + SERVER_PATH,
    )
    for line in iter(proc.stdout.readline, ""):
        if b"npm ERR!" in line:
            print(colored(line, "red"))
            print(
                f"[{colored('-','red')}] An error has occured while starting the server\nRestarting the server"
            )
            os.system("killall node")
            os.system("killall npm")
            sys.exit(-1)
        if b"Press CTRL-C to stop" in line:
            anim.complete()
            break


def initialize(videos, server, first=False):
    audio = convert_async(videos)

    for video in videos:

        if args.web:
            server.upload(video, video[:-3] + "ogg")
        else:
            server.addAudioPath(video, video[:-3] + "ogg")

        player.enqueue(video)
        
        if(first):
            server.create_room()
            player.play()
            player.pause()
            player.seek(0)
            
        
        server.add_track(video)


if __name__ == "__main__":

    signal.signal(signal.SIGINT, exitHandler)

    args = parse()
    args.localIP = getLocalIP()
    set_vars(args)

    if not args.web:
        spawn_server()

    player.launch()

    BaseManager.register("ServerConnection", ServerConnection)
    manager = BaseManager()
    manager.start()
    server = manager.ServerConnection()
    server.start_listening()

    Process(target=player.update, args=(server,)).start()

    initialize([args.f[0]], server=server, first=True)

    if len(args.f) > 1:
        Process(
            target=initialize,
            kwargs={"videos": args.f[1:], "server": server, "first": False},
        ).run()

    print("\n" + colored("#" * 70, "green") + "\n")
    while True:
        time.sleep(1)
