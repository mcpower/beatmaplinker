import requests


class Osu:
    """An osu! API wrapper."""
    def __init__(self, api_key):
        self.api_key = api_key

    def get_beatmap_info(self, map_tuple):
        """Gets information about a beatmap given a tuple of type and id."""
        map_type, map_id = map_tuple
        payload = {"k": self.api_key, map_type: map_id}
        r = requests.get("https://osu.ppy.sh/api/get_beatmaps", params=payload)
        out = r.json()
        if "error" in out:
            raise Exception("osu!api returned an error of " + out["error"])
        return out
