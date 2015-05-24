import re
import html
import praw
import requests
import configparser
import os
import urllib.parse
from functools import lru_cache
from limitedset import LimitedSet


if not os.path.exists("config.ini"):
    print("No config file found.")
    print("Copy config_example.ini to config.ini and modify to your needs.")
    exit()

config = configparser.ConfigParser()
config.read("config.ini")

CACHE_SIZE = int(config.get("bot", "max_cache"))
URL_REGEX = re.compile(r'<a href="(?P<url>https?://osu\.ppy\.sh/[^"]+)">(?P=url)</a>')  # NOQA


@lru_cache(maxsize=CACHE_SIZE)
def get_beatmap_info(map_type, map_id):
    """Gets information about a beatmap given a URL.

    Cached helper function to try to minimize osu! api requests.
    """
    payload = {"k": config.get("osu", "api_key"), map_type: map_id}
    r = requests.get("https://osu.ppy.sh/api/get_beatmaps", params=payload)
    out = r.json()
    if "error" in out:
        raise Exception("osu!api returned an error of " + out["error"])
    return out

def seconds_to_string(seconds):
    return "{0}:{1:0>2}".format(*divmod(seconds, 60))

def format_url(url):
    """Formats an osu.ppy.sh URL for a comment.

    Possible URL formats:
        https://osu.ppy.sh/p/beatmap?b=115891&m=0#
        https://osu.ppy.sh/b/244182
        https://osu.ppy.sh/p/beatmap?s=295480
        https://osu.ppy.sh/s/295480

    Returns False if not in the correct format.
    """
    parsed = urllib.parse.urlparse(url)
    map_type, map_id = "", ""

    if parsed.path.startswith("/b/"):
        map_type, map_id = "b", parsed.path[3:]
    elif parsed.path.startswith("/s/"):
        map_type, map_id = "s", parsed.path[3:]
    elif parsed.path == "/p/beatmap":
        query = urllib.parse.parse_qs(parsed.query)
        if "b" in query:
            map_type, map_id = "b", query["b"][0]
        elif "s" in query:
            map_type, map_id = "s", query["s"][0]
        else:
            return False
    else:
        return False

    info = dict(get_beatmap_info(map_type, map_id)[0])  # create new instance
    info["difficultyrating"] = float(info["difficultyrating"])
    info["hit_length"] = seconds_to_string(int(info["hit_length"]))
    info["total_length"] = seconds_to_string(int(info["total_length"]))

    if map_type == "b":  # single map
        return config.get("template", "map").format(**info)
    if map_type == "s":  # beatmap set
        return config.get("template", "mapset").format(**info)


def format_comment(urls):
    """Formats a list of osu.ppy.sh URLs into a comment.

    URLs do not need to be valid beatmap URLs.
    """
    seen = set()
    urls_without_dups = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            urls_without_dups.append(url)

    return "{0}\n\n{1}\n\n{2}".format(
        config.get("template", "header"),
        "\n  ".join(map(format_url, filter(None, urls_without_dups))),
        config.get("template", "footer")
    )


def get_urls_from_comment(comment):
    """Extracts all bare osu.ppy.sh URLs from a comment."""
    return URL_REGEX.findall(html.unescape(comment))

r = praw.Reddit(user_agent=config.get("reddit", "user_agent"))
# r.login(config.get("reddit", "username"), config.get("reddit", "password"))

seen_comments = LimitedSet(CACHE_SIZE)
subreddit = config.get("reddit", "subreddit")

comments = r.get_comments(subreddit)
