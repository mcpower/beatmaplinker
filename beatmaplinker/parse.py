import html
import urllib.parse
import re

URL_REGEX = re.compile(r'<a href="(?P<url>https?://osu\.ppy\.sh/[^"]+)">(?P=url)</a>')  # NOQA


def get_map_params(url):
    """Returns a tuple of (map_type, map_id) or False if URL is invalid.

    Possible URL formats:
        https://osu.ppy.sh/p/beatmap?b=115891&m=0#
        https://osu.ppy.sh/b/244182
        https://osu.ppy.sh/p/beatmap?s=295480
        https://osu.ppy.sh/s/295480
    """
    parsed = urllib.parse.urlparse(url)

    map_type, map_id = None, None
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
    if map_id is not None and "&" in map_id:
        map_id = map_id[:map_id.index("&")]
    if map_type and map_id.isdigit():
        return map_type, map_id
    return False


def get_links_from_html(html_string):
    """Returns a list of all osu! URLs from a HTML string."""
    return [html.unescape(z) for z in URL_REGEX.findall(html_string)]
