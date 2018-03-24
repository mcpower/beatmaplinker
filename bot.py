import sys
import time
from beatmaplinker import format, osu, parse, reddit, tillerino
from beatmaplinker import helpers as h
from beatmaplinker.structs import LimitedSet, ConfigParser


class Bot:
    def __init__(self, config, replace):
        try:
            self.reddit = reddit.Reddit(**config["reddit"])
            self.osu = osu.Osu(**config["osu"])
            self.formatter = format.Formatter(replace, **config["template"])
            self.tillerino = tillerino.Tillerino(**config["tillerino"])

            bot_sect = config["bot"]
            self.max_comments = int(bot_sect["max_comments"])
            self.seen_comments = LimitedSet(2 * self.max_comments)
            self.max_submissions = int(bot_sect["max_submissions"])
            self.seen_submissions = LimitedSet(2 * self.max_submissions)
            self.extra_delay = int(bot_sect.get("extra_delay", 0))
            self.meme = bot_sect.get("meme", None)
        except Exception as e:
            print("We had an exception when parsing the config.")
            print("Have you configured config.ini correctly?")
            print("The error caught was:")
            print(e)
            sys.exit()

    def scan_content(self, thing_type, content, seen):
        """Scans content for new things to reply to."""
        for thing in content:
            if thing.id in seen:
                continue  # already reached up to here before
            cur_id = thing.id
            found = list(h.compose(
                reddit.get_html_from_thing,
                parse.get_links_from_html,
                h.mapf(parse.get_map_params),
                h.truthies,
                h.remove_dups
            )(thing))

            if not found:
                # print("New", thing_type, thing.id, "with no maps.")
                if thing.id != cur_id:
                    print("thing id changed, not found")
                    continue
                seen.add(thing.id)
                continue
            if self.reddit.has_replied(thing):
                print("We've replied to", thing_type, thing.id, "before!")
                if thing.id != cur_id:
                    print("thing id changed, has replied")
                    continue
                seen.add(thing.id)
                continue  # we reached here in a past instance of this bot

            if len(found) > 300:
                comments = ["Too many maps.\n\n" + self.formatter.footer]
                print("thing:", thing.id, "too many maps.")
                if thing.id != cur_id:
                    print("thing id changed, too many maps")
                    continue
                self.reddit.reply(thing, comments)
                seen.add(thing.id)
            else:
                map_info = list(map(self.osu.get_beatmap_info, found))
                pp_info = list(map(self.tillerino.get_pp_info, map_info))
                map_strings = list(map(self.formatter.format_map,
                                       map_info, pp_info))
                is_selfpost = thing_type == "submission"
                is_meme = (self.meme is not None and
                           sum(self.meme in s for s in map_strings) > 1)

                comments = self.formatter.format_comments(map_strings,
                                                          selfpost=is_selfpost,
                                                          meme=is_meme)
                print("thing:", thing.id, "found:", found)
                if thing.id != cur_id:
                    print("thing id changed, normal comment")
                    continue
                self.reddit.reply(thing, comments)
                seen.add(thing.id)

    def scan_loop(self):
        while True:
            try:
                self.scan_content(
                    "comment",
                    self.reddit.get_comments(self.max_comments),
                    self.seen_comments)

                self.scan_content(
                    "submission",
                    self.reddit.get_submissions(self.max_submissions),
                    self.seen_submissions)

                time.sleep(3 + self.extra_delay)
            except KeyboardInterrupt:
                print("Stopping the bot.")
                sys.exit()
            except Exception as e:
                print("We caught an exception! It says:")
                print(e)
                print("Sleeping for 15 seconds.")
                time.sleep(15)
                continue


def main():
    config = ConfigParser()
    with open("config_default.ini", encoding="utf8") as c:
        config.read_file(c)
    read_files = config.read("config.ini", encoding="utf8")

    if not read_files:
        print("We couldn't find config.ini!")
        print("Copy config_example.ini to config.ini and edit to your needs.")
        print("You can also override config_default.ini in there too!")
        sys.exit()

    replacements = ConfigParser()
    with open("replacements_default.ini", encoding="utf8") as r:
        replacements.read_file(r)
    replacements.read("replacements.ini", encoding="utf8")

    bot = Bot(config, replacements)
    bot.scan_loop()


if __name__ == '__main__':
    main()
