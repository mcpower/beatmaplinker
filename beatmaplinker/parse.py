import html
import urllib.parse
import re

URL_REGEX = re.compile(r'<a href="(?P<url>https?://(?:osu|old)\.ppy\.sh/[^"]+)">(?P=url)</a>')  # NOQA
NEW_SITE_PATH = "/beatmapsets/"


def get_map_params(url):
    """Returns a tuple of (map_type, map_id) or None if URL is invalid.
    Possible URL formats:
        https://osu.ppy.sh/p/beatmap?b=115891&m=0#
        https://osu.ppy.sh/b/244182
        https://osu.ppy.sh/p/beatmap?s=295480
        https://osu.ppy.sh/s/295480

        https://osu.ppy.sh/beatmapsets/89888#osu/244182
        https://osu.ppy.sh/beatmapsets/781006/#osu/1640424
    
    Assume maps on new site link to the set, not the specific map.
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
    elif parsed.path.startswith(NEW_SITE_PATH):
        # The map selection is given in parsed as "fragment".
        # Ignore this, as we are assuming it's linking to the set.
        map_type, map_id = "s", parsed.path[len(NEW_SITE_PATH):]

    if map_id is None:
        return

    if "&" in map_id:
        # I think this should never happen.
        map_id = map_id[:map_id.index("&")]

    map_id = map_id.rstrip("/")

    if map_type and map_id.isdigit():
        return map_type, map_id


def get_links_from_html(html_string):
    """Returns a list of all osu! URLs from a HTML string."""
    return [html.unescape(z) for z in URL_REGEX.findall(html_string)]
