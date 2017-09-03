import requests

API_URL = "https://api.tillerino.org/beatmapinfo"
DEFAULT_API_KEY = "00000000000000000000000000000000"
ALLOWED_MODES = {"0"}
ALLOWED_APPROVED = {"2", "1"}


class Tillerino:
    """A Tillerino API wrapper."""
    def __init__(self, api_key=DEFAULT_API_KEY, wait=1000):
        self.api_key = api_key
        self.wait = wait

    def get_pp_info(self, map_info):
        """Gets PP info about a specific beatmap."""
        if self.api_key == DEFAULT_API_KEY or len(map_info) != 1:
            return {}

        map_dict = map_info[0]

        if (map_dict["mode"] not in ALLOWED_MODES or
                map_dict["approved"] not in ALLOWED_APPROVED):
            return {}

        payload = {
            "k": self.api_key,
            "wait": self.wait,
            "beatmapid": map_dict["beatmap_id"]
        }
        try:
            r = requests.get(API_URL, params=payload)
        except Exception as e:
            print("tillerino:", e)
            return {}
        if r.status_code != 200:
            print(r.status_code, "occurred when getting pp data for",
                  map_dict["beatmap_id"])
            return {}

        # Tillerino returns a in a weird format, so let's convert that to a
        # dictionary to make our lives easier
        key_value_list = r.json()["ppForAcc"]["entry"]
        output_dict = {str(d["key"]): d["value"] for d in key_value_list}
        return output_dict
