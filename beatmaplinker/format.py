from functools import reduce

MODES = [
    ("0", "Standard"),
    ("1", "Taiko"),
    ("2", "CtB"),
    ("3", "Mania")
]


class Formatter:
    def __init__(self, replacements, mapset, map, header="", footer="",
                 selfpost_header=None, selfpost_footer=None, meme_header=None,
                 meme_footer=None, sep="\n\n", char_limit=10000, diff="",
                 diffs=""):
        self.replacements = replacements
        self.header = header
        self.footer = footer

        self.selfpost_header = selfpost_header
        self.selfpost_footer = selfpost_footer
        self.meme_header = meme_header
        self.meme_footer = meme_footer

        self.mapset = mapset
        self.map = map
        self.sep = sep
        self.char_limit = char_limit
        self.sep = self.sep.replace("\\n", "\n")

        self.diff = diff
        self.diffs = diffs

    def format_map(self, map_info):
        """Formats a map for a comment given a array of dicts.

        Array of dicts is in the format of osu! API responses.
        """
        if not map_info:  # invalid beatmap
            return "Invalid map."
        info = dict(map_info[0])  # create new instance, just in case.

        info["difficultyrating"] = float(info["difficultyrating"])
        info["hit_length"] = seconds_to_string(int(info["hit_length"]))
        info["total_length"] = seconds_to_string(int(info["total_length"]))

        diff_strings = []
        for num, mode in MODES:
            difficulties = [float(diff["difficultyrating"])
                            for diff in map_info
                            if diff["mode"] == num]
            if not difficulties:
                continue
            diff_dict = {
                "lowest_diff": min(difficulties),
                "highest_diff": max(difficulties),
                "diffs": len(difficulties),
                "mode": mode
            }

            if diff_dict["diffs"] == 1:
                diff_strings.append(self.diff.format(**diff_dict))
            else:
                diff_strings.append(self.diffs.format(**diff_dict))

        info["diff_display"] = "\n".join(diff_strings)

        # Sanitised inputs
        for key in ["artist", "creator", "source", "title", "version"]:
            info[key] = sanitise_md(info[key])

        for sect in self.replacements.sections():
            section_obj = self.replacements[sect]
            info[sect] = section_obj[info[section_obj["_key"]]].format(**info)

        if len(map_info) == 1:  # single map
            return self.map.format(**info)
        else:  # beatmap set
            return self.mapset.format(**info)

    def format_comments(self, maps, selfpost=False, meme=False):
        """Formats a list of map strings into a list of comments."""
        header = self.header
        footer = self.footer
        if selfpost:
            if self.selfpost_header is not None:
                header = self.selfpost_header
            if self.selfpost_footer is not None:
                footer = self.selfpost_footer
        if meme:
            if self.meme_header is not None:
                header = self.meme_header
            if self.meme_footer is not None:
                footer = self.meme_footer

        line_break = "\n\n"
        if header:
            bodies = [header + line_break]  # start w/ header
        else:
            bodies = [""]

        f_len, s_len, b_len = map(len, [footer, self.sep, line_break])

        if self.footer:
            f_len += b_len  # footer will always be with a line break
        else:
            f_len = 0

        first_map = True
        for beatmap in maps:
            next_len = len(bodies[-1]) + len(beatmap) + f_len

            if not first_map:  # first map of comment means no separator
                next_len += s_len

            new_comment_after = False
            if next_len > self.char_limit:  # comment char limit
                if next_len - f_len > self.char_limit or beatmap is maps[-1]:
                    bodies.append("")
                    first_map = True
                else:
                    # we cram it in by removing footer + it's not the last map
                    # sometimes I wish Python had a defer statement
                    new_comment_after = True

            if first_map:
                first_map = False
            else:
                bodies[-1] += self.sep
            bodies[-1] += beatmap

            if new_comment_after:
                bodies.append("")
                first_map = True

        if footer:
            bodies[-1] += line_break + footer
        return bodies


def seconds_to_string(seconds):
    """Returns a m:ss representation of a time in seconds."""
    return "{0}:{1:0>2}".format(*divmod(seconds, 60))


def sanitise_md(string):
    """Escapes any markdown characters in string."""
    emphasis = "*_"
    escaped = reduce(lambda a, b: a.replace(b, "&#{:0>4};".format(ord(b))),
                     emphasis, string)
    other_chars = list("\\[]^") + ["~~"]
    escaped = reduce(lambda a, b: a.replace(b, "\\" + b), other_chars, escaped)
    return escaped
