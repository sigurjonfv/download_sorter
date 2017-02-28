from os import listdir, walk
import os
from os import path
import re
import enchant
import shutil

# Hynek Schlawack - first v2.0.1
def first(iterable, default=None, key=None):
    if key is None:
        for el in iterable:
            if el:
                return el
    else:
        for el in iterable:
            if key(el):
                return el
    return default

# Testing
try:
    shutil.rmtree("/Users/viktor/Desktop/downloads")
except:
    print("Something failed when clearing source directory")
try:
    shutil.rmtree("/Users/viktor/Desktop/sorted")
except:
    print("Something failed when clearing destination directory")
shutil.copytree("/Users/viktor/Downloads/downloads", "/Users/viktor/Desktop/downloads")
input("Give the go-ahead")

d = enchant.Dict("en_US")
VERBOSE = False

def pr(*args):
    if VERBOSE:
        print(" ".join(map(str, args)))

def find_season(s):
    s = s.lower()
    search = re.search("s(\d+)", s)
    if search:
        pr("Found season", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search("season\s*(\d+)", s)
    if search:
        pr("Found season", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search("(\d+)x\d+", s)
    if search:
        pr("Found season", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search("[^a-zA-Z0-9\(\[](\d+)[^a-zA-Z0-9\)\]]", s)
    if search:
        season = search.groups()[0]
        if 2017 > int(season) > 1900:
            pr("Season is probably year", season, "in: '", s, "'")
            return None
        season = season[:len(season) // 2]
        pr("Found sketchy season", season, "in: '", s, "'")
        return season
    return None

def find_episode(s):
    s = s.lower()
    search = re.search("e(\d+)", s)
    if search:
        pr("Found episode", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search("\d+x(\d+)", s)
    if search:
        pr("Found episode", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search("episode\s*(\d+)", s)
    if search:
        pr("Found episode", search.groups()[0], "in: '", s, "'")
        return search.groups()[0]
    search = re.search(r"[^a-zA-Z0-9\(\[](\d+)[^a-zA-Z0-9\)\]]", s)
    if search:
        episode = search.groups()[0]
        if 2017 > int(episode) > 1900:
            pr("Episode is probably year", episode, "in: '", s, "'")
            return None
        episode = episode[len(episode) // 2:]
        pr("Found sketchy episode", episode, "in: '", s, "'")
        # Remove 0 padding
        return str(int(episode))
    return None

def find_name(s, is_show=True):
    # Remove 1080p, 720p etc.
    s = re.sub(r"\d+p", "", s)
    # Don't consider anything after the season to be part of the name
    parts = re.split(r"\s*s\s*\d+\s*e\s*\d+\s*|\s*season\s*\d+|\d+\s*x\s*\d+", s, flags=re.IGNORECASE)
    s = first(parts, key = lambda x: bool(x))
    # Find all simple words or numbers in the name
    words = re.findall(r"([A-Za-z'0-9]+|[0-9]+)", s)
    valid_words = []
    last_index = 0
    # Once we've found a number which would indicate a season, episode or year we don't add to the name
    no_numbers = True
    for i, w in enumerate(words):
        if w.isdigit():
            no_numbers = False
            if not is_show:
                valid_words.append(w)
        elif no_numbers or d.check(w):
            valid_words.append(w.lower())
            last_index = i
        else:
            break
    name = " ".join(valid_words)
    return name

video_file_extensions = set(["avi", "mkv", "mp4", "wmv", "mng", "mov", "qt", "flv", "webm", "m4p", "m4v", "mpg", "mp2", "mpeg", "mpe", "mpv"])
def is_video_extension(extension):
    return extension in video_file_extensions

junk_extension_extensions = set(["nfo", "txt"])
def is_junk_file(extension):
    return extension in junk_extension_extensions

subtitle_file_extensions = set(["sub", "srt", "sbv"])
def is_subtitle_extension(extension):
    return extension in subtitle_file_extensions

base = "/Users/viktor/Desktop/sorted"
if not os.path.exists(base):
    os.makedirs(base)
for root, dirs, files in walk('/Users/viktor/Desktop/downloads', topdown=False):
    for f in files:
        name = find_name(f)
        episode = find_episode(f)
        season = find_season(f)
        if name and season and episode:
            # Remove 0's at front
            season = str(int(find_season(f)))
            season_show_dir = os.path.join(base, name, "season " + season)
            if not os.path.exists(season_show_dir):
                os.makedirs(season_show_dir)
            shutil.move(os.path.join(root, f), os.path.join(season_show_dir, f))
        else:
            print("*****Can't find a match for", root+"/"+f)
            print("name:", name)
            print("episode:", episode)
            print("season:", season)

vesen = ""
"The Making of QI WS PDTV [SKID].avi"
"The Lincoln lawyer [ODI].mp4"
"santi-dexterd07e10.hdrip.xvid.avi"
"Bored to Death #07 - The Case of the Stolen Sperm.avi"

print(find_name("8 Out of 10 Cats Uncut S12E02 WS PDTV [SKID].avi"))
print(find_name("Bored to Death Season 2 Complete"))
print(find_name("downton_abbey.3x06.hdtv_x264-fov.mp4"))
print(find_name("desperate.housewives.809.hdtv-lol.avi"))
print(find_name("desperate.housewives.1809.hdtv-lol.avi"))
print(find_name("desperate.housewives.11809.hdtv-lol.avi"))
print(find_name("desperate.housewives.111809.hdtv-lol.avi"))
print (find_name("desperate.housewives.(2011).hdtv-lol.avi"))
print (find_name("desperate.housewives.(2016).hdtv-lol.avi"))
print (find_name("easy.a.2010.bdrip.xvid-imbt.avi"))
print (find_name("Dredd.2012.1080p.BluRay.x264-SPARKS.avi"))
print (find_name("Run Fat Boy Run[2007]DvDrip[Eng]-FXG.avi"))

print(find_episode("8 Out of 10 Cats Uncut S12E02 WS PDTV [SKID].avi"))
print(find_episode("Bored to Death Season 2 Complete"))
print(find_episode("downton_abbey.3x06.hdtv_x264-fov.mp4"))
print(find_episode("desperate.housewives.809.hdtv-lol.avi"))
print(find_episode("desperate.housewives.1809.hdtv-lol.avi"))
print(find_episode("desperate.housewives.11809.hdtv-lol.avi"))
print(find_episode("desperate.housewives.111809.hdtv-lol.avi"))
print (find_episode("desperate.housewives.(2011).hdtv-lol.avi"))
print (find_episode("desperate.housewives.(2016).hdtv-lol.avi"))
print (find_episode("easy.a.2010.bdrip.xvid-imbt.avi"))
print (find_episode("Dredd.2012.1080p.BluRay.x264-SPARKS.avi"))

print(find_season("8 Out of 10 Cats Uncut S12E02 WS PDTV [SKID].avi"))
print(find_season("Bored to Death Season 2 Complete"))
print(find_season("downton_abbey.3x06.hdtv_x264-fov.mp4"))
print(find_season("desperate.housewives.809.hdtv-lol.avi"))
print(find_season("desperate.housewives.1809.hdtv-lol.avi"))
print(find_season("desperate.housewives.11809.hdtv-lol.avi"))
print(find_season("desperate.housewives.111809.hdtv-lol.avi"))
print (find_season("desperate.housewives.(2011).hdtv-lol.avi"))
print (find_season("desperate.housewives.(2016).hdtv-lol.avi"))
print (find_season("easy.a.2010.bdrip.xvid-imbt.avi"))
print (find_season("Dredd.2012.1080p.BluRay.x264-SPARKS.avi"))
