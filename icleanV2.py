import os
import shutil
import time
import sys
import re
import argparse

from guessit import guessit

video_file_extensions = set(["avi", "mkv", "divx", "mp4", "wmv", "mng", "mov", "qt", "flv", "webm", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv"])
junk_file_extensions = set(["nfo", "txt", "part", "torrent", "dat", "mta", "rm", "DS_Store", "lnk", "ignore", "ini", "db"])
subtitle_file_extensions = set(["sub", "srt", "sbv"])
audio_file_extensions = set(["mp3", "ogg", "flac", "midi", "mid", "m4a", "wma", "aac"])
picture_file_extensions = set(["gif", "jpg", "jpeg", "gif", "png"])

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument("source", help="download folder that you want to sort")
parser.add_argument("dest", help="path to sorted folder")
parser.add_argument("-v", action="store_true", help="show a lot of output")
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

def pr(*prints):
    if args.get("v"):
        print(" ".join(map(str, prints)))


start = time.time()
file_counter = 0

source = args.get("source")
destination = args.get("dest")

movie_folder = os.path.join(destination, "movies")
tv_folder = os.path.join(destination, "shows")
audio_folder = os.path.join(destination, "audio")
picture_folder = os.path.join(destination, "pictures")

if not os.path.exists(movie_folder):
    os.makedirs(movie_folder)
if not os.path.exists(tv_folder):
    os.makedirs(tv_folder)
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)
if not os.path.exists(picture_folder):
    os.makedirs(picture_folder)

input("Press any button to start")

def process_video_file(root, f, res):
    absolute_path = os.path.join(root, f)
    if res["type"] == "movie":
        # If we can't find a title then we move the file to the root movie folder
        movie_dir = os.path.join(movie_folder, res.get("title", ""))
        if not os.path.exists(movie_dir):
            os.makedirs(movie_dir)
        shutil.move(absolute_path, os.path.join(movie_dir, f))
    elif res["type"] == "episode":
        # If we can't find a title then we move the file to the base tv show folder
        title = res.get("title")
        if title == None:
            shutil.move(absolute_path, os.path.join(tv_folder, f))
        else:
            # If we can't find a season then we move the file to the tv shows folder
            season_show_dir = os.path.join(tv_folder, title)
            season = res.get("season")
            if season != None:
                season_show_dir = os.path.join(season_show_dir, "season " + str(season))
            if not os.path.exists(season_show_dir):
                os.makedirs(season_show_dir)
            shutil.move(absolute_path, os.path.join(season_show_dir, f))

for root, dirs, files in os.walk(source, topdown=False):
    # If we find an outtakes or extras folder we do other stuff
    relative_path = root[len(source) + 1:]
    modified_root, count = re.subn("outtakes|bloopers?|extras", "", relative_path, flags=re.IGNORECASE)
    extras_title = None
    if count != 0:
        res = guessit(modified_root)
        extras_title = res.get("title", "")
    for f in files:
        file_counter += 1
        if file_counter % 100 == 0:
            sys.stdout.write("\rfiles processed: " + str(file_counter))

        absolute_path = os.path.join(root, f)
        extension = f.split(".")[-1]

        if "sample" in f.lower():
            # Delete samples
            os.remove(absolute_path)
        elif extension in junk_file_extensions:
            os.remove(absolute_path)
        elif extension in audio_file_extensions:
            # Keep folder structure for audio files
            audio_dir = os.path.join(audio_folder, relative_path)
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
            shutil.move(absolute_path, os.path.join(audio_dir, f))
        elif extension in picture_file_extensions:
            # Move all pictures to one base picture folder
            shutil.move(absolute_path, os.path.join(picture_folder, f))
        # Guess from the file name first
        elif extension in video_file_extensions or extension in subtitle_file_extensions:
            search_string = relative_path + os.path.sep + f
            # If there is /Subtitle in the path of the subtitle then it is sorted incorrectly
            search_string = re.sub(os.path.sep + "(subtitles?|subs?)", "", search_string, flags=re.IGNORECASE)
            res = guessit(search_string)
            # Make corrections here
            if res.get("title") in corrections:
                correct = corrections.get(res.get("title"))
                for key in correct:
                    res[key] = correct[key]
            elif extras_title:
                res["title"] = extras_title
                if "season" in res:
                    del res["season"]
            pr(f)
            pr(search_string)
            pr(res)
            process_video_file(root, f, res)
        else:
            pr("Did not process", relative_path + os.path.sep + f)
    for folder in dirs:
        absolute_path = os.path.join(root, folder)
        try:
            os.rmdir(absolute_path)
        except:
            pr("Directory not empty", absolute_path)

end = time.time()

print("\nSorting", file_counter, "files was completed in", end - start, "seconds.")
