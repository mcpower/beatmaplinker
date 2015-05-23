import re
import html
import praw
import requests
import configparser
import os
import shutil
from limitedset import LimitedSet


if not os.path.exists("config.ini"):
    print("No config file found. Copying from config_example.ini...")
    shutil.copyfile("config_example.ini", "config.ini")

config = configparser.ConfigParser()
config.read("config.ini")


def format_url(url):
    """Formats an osu.ppy.sh URL for a comment."""
    return url


def format_comment(urls):
    """Formats a list of osu.ppy.sh URLs into a comment."""
    return "{0}\n\n{1}\n\n{2}".format(
        config.get("template", "header"),
        "\n  ".join(map(format_url, urls)),
        config.get("template", "footer")
    )


r = praw.Reddit(user_agent=config.get("reddit", "user_agent"))

seen_comments = LimitedSet(int(config.get("bot", "max_cache")))

# r.login(config.get("reddit", "username"), config.get("reddit", "password"))
