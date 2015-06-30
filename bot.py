import sys
import time
from beatmaplinker import format, osu, parse, reddit
from beatmaplinker import helpers as h
from beatmaplinker.structs import LimitedSet, ConfigParser


class Bot:
    def __init__(self, config, replacements):
        try:
            self.reddit = reddit.Reddit(**config["reddit"])
            self.osu = osu.Osu(**config["osu"])
            self.formatter = format.Formatter(replacements, **config["template"])

            bot_sect = config["bot"]
            self.max_comments = int(bot_sect["max_comments"])
            self.seen_comments = LimitedSet(self.max_comments + 100)
            self.max_submissions = int(bot_sect["max_submissions"])
            self.seen_submissions = LimitedSet(self.max_submissions + 50)
        except Exception as e:
            # print("We had an exception when parsing the config.")
            # print("Have you configured config.ini correctly?")
            # print("The error caught was:")
            # print(e)
            raise e
            sys.exit()

    def scan_content(self, thing_type, content, seen):
        """Scans content for new things to reply to."""
        for thing in content:
            if thing.id in seen:
                break  # already reached up to here before
            seen.add(thing.id)
            found = list(h.compose(
                reddit.get_html_from_thing,
                parse.get_links_from_html,
                h.mapf(parse.get_map_params),
                h.truthies,
                h.remove_dups
            )(thing))

            if not found:
                print("New", thing_type, thing.id, "with no maps.")
                continue
            if self.reddit.has_replied(thing):
                print("We've replied to", thing_type, thing.id, "before!")
                break  # we reached here in a past instance of this bot

            if len(found) > 300:
                comments = ["Too many maps.\n\n" + self.formatter.footer]
            else:
                map_strings = map(h.compose(
                    self.osu.get_beatmap_info,
                    self.formatter.format_map
                ), found)
                comments = self.formatter.format_comments(map_strings)

            self.reddit.reply(thing, comments)

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

                time.sleep(3)
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
    with open("config_default.ini") as c:
        config.read_file(c)
    read_files = config.read("config.ini")

    if not read_files:
        print("We couldn't find config.ini!")
        print("Copy config_example.ini to config.ini and edit to your needs.")
        print("You can also override config_default.ini in there too!")
        sys.exit()

    replacements = ConfigParser()
    with open("replacements_default.ini") as r:
        replacements.read_file(r)
    replacements.read("replacements.ini")

    bot = Bot(config, replacements)
    bot.scan_loop()


if __name__ == '__main__':
    main()
