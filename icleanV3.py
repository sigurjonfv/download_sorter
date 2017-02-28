import os
import shutil
import time
import sys
import re
import argparse
from itertools import groupby
from guessit import guessit

# Default division of file extensions
video_file_extensions = set(["avi", "mkv", "divx", "mp4", "wmv", "mng", "mov", "qt", "flv", "webm", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv"])
junk_file_extensions = set(["nfo", "txt", "part", "torrent", "dat", "mta", "rm", "DS_Store", "lnk", "ignore", "ini", "db"])
subtitle_file_extensions = set(["sub", "srt", "sbv"])
audio_file_extensions = set(["mp3", "ogg", "flac", "midi", "mid", "m4a", "wma", "aac"])
picture_file_extensions = set(["gif", "jpg", "jpeg", "gif", "png"])

# Defining arguments for the program
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("source", help="download folder that you want to sort")
parser.add_argument("dest", help="path to sorted folder")
parser.add_argument("-v", action="store_true", help="show a lot of output")
parser.add_argument("-t", nargs='?', const=0, type=int, default=0,
                    help="""Defines how intelligent vs strict the tool is.\n\r
                    \t0: Intelligently determines information about files based on either file names or the folders they are in (Default and Recommended). \n\r
                    \t1: Semi-Intelligently only determines information about files based on file names only, except for titles, which may be determined by the folders they are in. \n\r
                    \t2 or higher: Strictly determines information about files based only on the file name, not the folder they are in.""")
parser.add_argument("-c", metavar="[path]",
                    help="""a path to a file with a correction on each line on the form:\n\t
                    [matched title]->[episode/movie]/[correct title]/[correct season]""")
parser.add_argument("-audio", metavar="[extension list]",
                    help="a list on the form \"one,two,three\", default:\n" + ",".join(audio_file_extensions))
parser.add_argument("-video", metavar="[extension list]",
                    help="a list on the form \"one,two,three\", default:\n" + ",".join(video_file_extensions))
parser.add_argument("-picture", metavar="[extension list]",
                    help="a list on the form \"one,two,three\", default:\n" + ",".join(picture_file_extensions))
parser.add_argument("-subtitle", metavar="[extension list]",
                    help="a list on the form \"one,two,three\", default:\n" + ",".join(subtitle_file_extensions))
parser.add_argument("-junk", metavar="[extension list]",
                    help="a list on the form \"one,two,three\" all items that match this extensions will be removed, default:\n" +
                    ",".join(junk_file_extensions))


def pr(*prints):
    """Prints if verbose"""
    if args.get("v"):
        print(" ".join(map(str, prints)))


# Read arguments
args = vars(parser.parse_args())

if args.get("audio"):
    audio_file_extensions = set(args["audio"].split(","))
if args.get("video"):
    video_file_extensions = set(args["video"].split(","))
if args.get("junk"):
    junk_file_extensions = set(args["junk"].split(","))
if args.get("picture"):
    picture_file_extensions = set(args["picture"].split(","))
if args.get("subtitle"):
    subtitle_file_extensions = set(args["subtitle"].split(","))

source = args.get("source")
destination = args.get("dest")

movie_folder = os.path.join(destination, "movies")
tv_folder = os.path.join(destination, "shows")
audio_folder = os.path.join(destination, "audio")
picture_folder = os.path.join(destination, "pictures")

strictness = args.get("t")

# Load corrections
corrections = {}
if args.get("c"):
    with open(args.get("c")) as correction:
        for line in correction.read().splitlines():
            # 8 Out-> episode/8 Out of 10 Cats/10
            title, to = line.split("->")
            to = to.split("/")
            entity = {}
            entity["type"] = to[0]
            if len(to) > 1:
                entity["title"] = to[1]
            if len(to) > 2:
                entity["season"] = int(to[2])
            corrections[title] = entity


start = time.time()
file_counter = 0

if not os.path.exists(movie_folder):
    os.makedirs(movie_folder)
if not os.path.exists(tv_folder):
    os.makedirs(tv_folder)
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)
if not os.path.exists(picture_folder):
    os.makedirs(picture_folder)

input("Press any button to start")


def process_audio_file(root, file_name, relative_path):
    """Moves audio files into the correct folder maintaining folder structure for audio files"""
    absolute_path = os.path.join(root, file_name)
    audio_dir = os.path.join(audio_folder, relative_path)
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
    shutil.move(absolute_path, os.path.join(audio_dir, file_name))


def process_picture_file(root, file_name):
    """Moves all pictures to one base picture folder"""
    absolute_path = os.path.join(root, file_name)
    shutil.move(absolute_path, os.path.join(picture_folder, file_name))


def process_video_file(root, file_name, res):
    """Does corrections and moves video files to corresponding folders"""
    # Make corrections:
    if res.get("title") in corrections:
        correct = corrections.get(res.get("title"))
        for key in correct:
            res[key] = correct[key]

    absolute_path = os.path.join(root, file_name)

    if res["type"] == "movie":
        # If we can't find a title then we move the file to the root movie folder
        title = res.get("title")
        if title == None:
            shutil.move(absolute_path, os.path.join(tv_folder, file_name))
        else:
            movie_dir = os.path.join(movie_folder, title)
            if not os.path.exists(movie_dir):
                os.makedirs(movie_dir)
            shutil.move(absolute_path, os.path.join(movie_dir, file_name))

    elif res["type"] == "episode":
        # If we can't find a title then we move the file to the base tv show folder
        title = res.get("title")
        if title == None:
            shutil.move(absolute_path, os.path.join(tv_folder, file_name))
        else:
            # If we can't find a season then we move the file to the tv shows folder
            season_show_dir = os.path.join(tv_folder, title)
            season = res.get("season")
            if season != None:
                season_show_dir = os.path.join(season_show_dir, "season " + str(season))
            if not os.path.exists(season_show_dir):
                os.makedirs(season_show_dir)
            shutil.move(absolute_path, os.path.join(season_show_dir, file_name))


def process_video_file_list(root, guessed_files_list):
    """Checks if file is the only one in a directory with its title. If so, checks the containing folders for
    the series title."""
    grouped_titles = groupby(guessed_video_files, lambda x: x[1].get("title"))
    for group in grouped_titles:
        group = (group[0], list(group[1]))
        if group[0] == None or len(group[1]) == 1:
            # Title is either None or only one item has that title, check containing folders for the series title
            new_res = guessit(relative_path)
            for file_name, res in group[1]:
                if strictness < 2:
                    try:
                        res['title'] = new_res['title']
                    except:
                        pass
                if strictness < 1 and new_res['type'] == 'episode':
                    for key in ['type', 'season', 'episode']:
                        try:
                            res[key] = new_res[key]
                        except:
                            pass
                process_video_file(root, file_name, res)
        else:
            for file_name, res in group[1]:
                process_video_file(root, file_name, res)


for root, dirs, files in os.walk(source, topdown=False):
    # If we find an outtakes or extras folder we do other stuff
    relative_path = root[len(source) + 1:]

    guessed_video_files = []
    for file_name in files:
        file_counter += 1
        if file_counter % 100 == 0:
            sys.stdout.write("\rfiles processed: " + str(file_counter))

        absolute_path = os.path.join(root, file_name)
        extension = file_name.split(".")[-1]

        if "sample" in file_name.lower():
            # Delete samples
            os.remove(absolute_path)
        elif extension in junk_file_extensions:
            # Delete junk
            os.remove(absolute_path)
        elif extension in audio_file_extensions:
            # Process audio files
            process_audio_file(root, file_name, relative_path)
        elif extension in picture_file_extensions:
            # Process picture files
            process_picture_file(root, file_name)
        # Guess from the file name first
        elif extension in video_file_extensions or extension in subtitle_file_extensions:
            # Prepare video and subtitle files for processing
            search_string = os.path.join(relative_path, file_name)
            # If there is /Subtitle in the path of the subtitle then it is sorted incorrectly
            search_string = re.sub(os.path.sep + r"(subtitles?|subs?)", "", search_string, flags=re.IGNORECASE)
            res = guessit(search_string)
            # Video files are handled specially afterwards in order to detect episodes that do not contain the series names correctly.
            guessed_video_files.append((file_name, res))

            pr(file_name)
            pr(search_string)
            pr(res)
        else:
            pr("Did not process", relative_path + os.path.sep + file_name)

    # Process the video and subtitle files all together
    process_video_file_list(root, guessed_video_files)

    # If a folder is empty, delete it
    for folder in dirs:
        absolute_path = os.path.join(root, folder)
        try:
            os.rmdir(absolute_path)
        except:
            pr("Directory not empty", absolute_path)

end = time.time()

print("\nSorting", file_counter, "files was completed in", format(end - start, '.2f'), "seconds.")
