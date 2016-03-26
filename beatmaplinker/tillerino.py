import requests

API_URL = "http://bot.tillerino.org:1666/beatmapinfo"
DEFAULT_API_KEY = "00000000000000000000000000000000"
ALLOWED_MODES = {"0"}


class Tillerino:
    """A Tillerino API wrapper."""
    def __init__(self, api_key=DEFAULT_API_KEY, wait=1000):
        self.api_key = api_key
        self.wait = wait

    def get_pp_info(self, map_info):
        """Gets PP info about a specific beatmap."""
        if self.api_key == DEFAULT_API_KEY or len(map_info) != 1:
            return {}

        if map_info[0]["mode"] not in ALLOWED_MODES:
            return {}

        payload = {
            "k": self.api_key,
            "wait": self.wait,
            "beatmapid": map_info[0]["beatmap_id"]
        }
        r = requests.get(API_URL, params=payload)
        if r.status_code != 200:
            print(r.status_code, "occurred when getting pp data for",
                  map_info[0]["beatmap_id"])
            return {}

        # Tillerino returns a in a weird format, so let's convert that to a
        # dictionary to make our lives easier
        key_value_list = r.json()["ppForAcc"]["entry"]
        output_dict = {str(d["key"]): d["value"] for d in key_value_list}
        return output_dict
