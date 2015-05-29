import re
import html
import praw
import requests
import configparser
import os
import urllib.parse
import time
from functools import lru_cache
from limitedset import LimitedSet
from functools import reduce


if not os.path.exists("config.ini"):
    print("No config file found.")
    print("Copy config_example.ini to config.ini and modify to your needs.")
    exit()

config = configparser.ConfigParser()
config.read("config.ini")

MAX_COMMENTS = int(config.get("bot", "max_comments"))
MAX_SUBMISSIONS = int(config.get("bot", "max_submissions"))
OSU_CACHE = int(config.get("bot", "osu_cache"))
URL_REGEX = re.compile(r'<a href="(?P<url>https?://osu\.ppy\.sh/[^"]+)">(?P=url)</a>')  # NOQA
APPROVED_STATUS = {
    "3": "Qualified",
    "2": "Approved",
    "1": "Ranked",
    "0": "Pending",
    "-1": "WIP",
    "-2": "Graveyard"
}
APPROVED_STATUS_FORMAT = {
    "3": "*",
    "2": "**",
    "1": "**",
    "0": "",
    "-1": "",
    "-2": "~~"
}


@lru_cache(maxsize=OSU_CACHE)
def get_beatmap_info(map_type, map_id):
    """Gets information about a beatmap given a type and id.

    Cached helper function to try to minimize osu! api requests.
    """
    payload = {"k": config.get("osu", "api_key"), map_type: map_id}
    r = requests.get("https://osu.ppy.sh/api/get_beatmaps", params=payload)
    out = r.json()
    if "error" in out:
        raise Exception("osu!api returned an error of " + out["error"])
    return out


def seconds_to_string(seconds):
    """Returns a m:ss representation of a time in seconds."""
    return "{0}:{1:0>2}".format(*divmod(seconds, 60))


def get_map_params(url):
    """Returns a tuple of (map_type, map_id) or False if URL is invalid.

    Possible URL formats:
        https://osu.ppy.sh/p/beatmap?b=115891&m=0#
        https://osu.ppy.sh/b/244182
        https://osu.ppy.sh/p/beatmap?s=295480
        https://osu.ppy.sh/s/295480
    """
    parsed = urllib.parse.urlparse(url)

    if parsed.path.startswith("/b/"):
        return ("b", parsed.path[3:])
    elif parsed.path.startswith("/s/"):
        return ("s", parsed.path[3:])
    elif parsed.path == "/p/beatmap":
        query = urllib.parse.parse_qs(parsed.query)
        if "b" in query:
            return ("b", query["b"][0])
        elif "s" in query:
            return ("s", query["s"][0])
    return False


def sanitise_md(string):
    """Escapes any markdown characters in string."""
    escape = list("\\[]*_") + ["~~"]
    return reduce(lambda a, b: a.replace(b, "\\" + b), escape, string)


def format_map(map_type, map_id):
    """Formats a map for a comment given its type and id."""
    map_info = get_beatmap_info(map_type, map_id)
    if not map_info:  # invalid beatmap
        return "Invalid map{}.".format(["", "set"][map_type == "s"])
    info = dict(map_info[0])  # create new instance
    info["approved_format"] = APPROVED_STATUS_FORMAT[info["approved"]]
    info["approved"] = APPROVED_STATUS[info["approved"]]
    info["difficultyrating"] = float(info["difficultyrating"])
    info["hit_length"] = seconds_to_string(int(info["hit_length"]))
    info["total_length"] = seconds_to_string(int(info["total_length"]))

    # Sanitised inputs
    for key in ["artist", "creator", "source", "title", "version"]:
        info[key] = sanitise_md(info[key])

    if len(map_info) == 1:  # single map
        return config.get("template", "map").format(**info)
    else:  # beatmap set
        return config.get("template", "mapset").format(**info)


def format_comment(maps):
    """Formats a list of (map_type, map_id) tuples into a comment."""
    seen = set()
    maps_without_dups = []
    for beatmap in maps:
        if beatmap not in seen:
            seen.add(beatmap)
            maps_without_dups.append(beatmap)

    return "{0}\n\n{1}\n\n{2}".format(
        config.get("template", "header"),
        "\n\n".join(map(lambda tup: format_map(*tup), maps_without_dups)),
        config.get("template", "footer")
    )


def get_maps_from_html(html_string):
    """Returns a list of all valid maps as (map_type, map_id) tuples
    from some HTML.
    """
    return list(filter(None, map(get_map_params,
                                 URL_REGEX.findall(html_string))))


def get_maps_from_thing(thing):
    """Returns a list of all valid maps as (map_type, map_id) tuples
    from a thing.
    """
    if isinstance(thing, praw.objects.Comment):
        body_html = thing.body_html
    elif isinstance(thing, praw.objects.Submission):
        if not thing.selftext_html:
            return []
        body_html = thing.selftext_html
    return get_maps_from_html(html.unescape(body_html))


def has_replied(thing, r):
    """Checks whether the bot has replied to a thing already.

    Apparently costly.
    Taken from http://www.reddit.com/r/redditdev/comments/1kxd1n/_/cbv4usl"""
    botname = config.get("reddit", "username")
    if isinstance(thing, praw.objects.Comment):
        replies = r.get_submission(thing.permalink).comments[0].replies
    elif isinstance(thing, praw.objects.Submission):
        replies = thing.comments
    return any(reply.author.name == botname for reply in replies)


def reply(thing, text):
    """Post a comment replying to a thing."""
    print("Replying to {c.author.name}, thing id {c.id}".format(c=thing))
    print()
    print(text)
    print()
    if isinstance(thing, praw.objects.Comment):
        thing.reply(text)
    elif isinstance(thing, praw.objects.Submission):
        thing.add_comment(text)
    print("Replied!")


def thing_loop(thing_type, content, seen, r):
    """Scans content for new things to reply to."""
    for thing in content:
        if thing.id in seen:
            break  # already reached up to here before
        seen.add(thing.id)
        found = get_maps_from_thing(thing)
        if not found:
            print("New", thing_type, thing.id, "with no maps.")
            continue
        if has_replied(thing, r):
            print("We've replied to", thing_type, thing.id, "before!")
            break  # we reached here in a past instance of this bot

        reply(thing, format_comment(found))


r = praw.Reddit(user_agent=config.get("reddit", "user_agent"))
r.login(config.get("reddit", "username"), config.get("reddit", "password"))

seen_comments = LimitedSet(MAX_COMMENTS + 100)
seen_submissions = LimitedSet(MAX_SUBMISSIONS + 50)
subreddit = r.get_subreddit(config.get("reddit", "subreddit"))


while True:
    try:
        thing_loop("comment", subreddit.get_comments(limit=MAX_COMMENTS),
                   seen_comments, r)
        thing_loop("submission", subreddit.get_new(limit=MAX_SUBMISSIONS),
                   seen_submissions, r)
    except KeyboardInterrupt:
        print("Stopping the bot.")
        exit()
    except Exception as e:
        print("We caught an exception! It says:")
        print(e)
        print("Sleeping for 15 seconds.")
        time.sleep(15)
        continue
