from functools import reduce


class Formatter:
    def __init__(self, replacements, header, footer, mapset, map, sep="\n\n",
                 char_limit=10000):
        self.replacements = replacements
        self.header = header
        self.footer = footer
        self.mapset = mapset
        self.map = map
        self.sep = sep
        self.char_limit = char_limit
        self.sep = self.sep.replace("\\n", "\n")

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

    def format_comments(self, maps):
        """Formats a list of map strings into a list of comments."""
        maps = list(maps)  # used for last map detection

        line_break = "\n\n"
        bodies = [self.header + line_break]  # start w/ header

        f_len, s_len, b_len = map(len, [self.footer, self.sep, line_break])
        f_len += b_len  # footer will always be with a line break

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

        bodies[-1] += line_break + self.footer
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
