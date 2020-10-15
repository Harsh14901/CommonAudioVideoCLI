import ffmpeg
import sys
import os
import subprocess
import re
from termcolor import colored
from multiprocessing import Pool
import time
from itertools import product

BITRATE = 1000 * 16


def path2title(path):
    return path.split("/")[-1:][0]


def get_multiplier(quality):
    """ A multiplier to decide bitrate from the quality string """

    if quality == "low":
        return 5
    elif quality == "medium":
        return 6
    elif quality == "good":
        return 7
    elif quality == "high":
        return 8
    return 6


def extract(path, quality="medium"):
    """ Extractor function utilizing ffmpeg to extract audio from a given video file """
    try:
        file = ffmpeg.input(path)
        output_path = path[:-3] + "ogg"
        if os.path.exists(output_path):
            print(
                f"[{colored('#','yellow')}] Audio file {colored(path2title(output_path),'green')} already exists"
            )
            return output_path
        print(
            f"\n[{colored('+','green')}] Extracting audio for file %s"
            % (colored(path2title(path), "green")),
            end="",
        )
        from util import Animation

        anim = Animation()
        file.audio.output(
            output_path,
            acodec="libvorbis",
            audio_bitrate=BITRATE * get_multiplier(quality),
            loglevel=0,
        ).run()
        anim.complete()
        print(
            f"[{colored('+','green')}] Extraction completed for file %s"
            % (colored(path2title(output_path), "green"))
        )

    except Exception as ex:
        print(
            f"[{colored('-','red')}] There was an error extracting the audio for path {colored(path2title(output_path),'green')}: ",
            ex,
        )
        sys.exit(-1)

    return output_path    
    

def convert2mkv(path):
    out_path = path + ".mkv"
    if os.path.exists(out_path):
        return out_path
    try:
        from util import Animation

        anim = Animation()
        ffmpeg.input(path).output(out_path, codec="copy", loglevel=0).run()
        anim.complete()
        print(
            f"[{colored('+','green')}] Successfully converted {colored(path2title(out_path),'green')} to MKV format"
        )
        return out_path
    except Exception as e:
        print(
            f"[{colored('-','red')}] An error occured while converting {colored(path2title(out_path),'green')} to MKV: ",
            e,
        )
        raise e

def convert_async(paths, args):
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
