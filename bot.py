import multiprocessing as mp
import multiprocessing.connection as mpc
import sys
import time
from beatmaplinker import format, osu, parse, reddit, tillerino
from beatmaplinker import helpers as h
from beatmaplinker.structs import LimitedSet, ConfigParser


class Bot:
    def __init__(self, config, replace):
        try:
            self.config = config
            # Note: this reddit instance may not be used!
            self.reddit = self.get_new_reddit()
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

    def get_new_reddit(self):
        return reddit.Reddit(**self.config["reddit"])

    def scan_content(self, thing_type, content, seen, reddit_instance=None):
        """Scans content for new things to reply to."""
        if reddit_instance is None:
            reddit_instance = self.reddit

        for thing in content:
            self.process_content(thing_type, thing, seen, reddit_instance)

    def scan_content_stream(self, thing_type):
        """
        Scans content using PRAW streams and catch errors.
        This is better than scan_loop as PRAW has its own optimisations to
        reduce network / CPU usage, see
        https://github.com/praw-dev/praw/blob/ceb8acde155af72b98adbac7b2fc3aa9f596bb9e/praw/models/util.py#L167-L168
        """
        # Note that a seen set is not that useful here as PRAW keeps its own,
        # but as PRAW's stream may crash we still want to keep it around.

        # Additionally, we create a new reddit instance for the stream.
        # This is because requests.Session may not be thread safe, see
        # https://praw.readthedocs.io/en/v5.4.0/getting_started/multiple_instances.html
        # We don't use requests.Session for any other API wrappers,
        # so those should be thread safe - no state is mutated, only read.
        reddit_instance = self.get_new_reddit()
        if thing_type == "comment":
            content_factory = reddit_instance.get_comment_stream
        else:
            content_factory = reddit_instance.get_submission_stream

        # We want the seen set to stay local to the method call / process,
        # as if this process is terminated while global state is being
        # mutated, bad things may(?) occur.
        seen = LimitedSet(300)

        while True:
            try:
                print("Starting", thing_type, "streaming.")
                for thing in content_factory():
                    try:
                        self.process_content(thing_type, thing, seen, reddit_instance)
                    except Exception as e:
                        print("We caught an exception when processing a thing! It says:")
                        print(e)
                        print("The {} in question was {}".format(thing_type, thing.id))
                        continue
            except Exception as e:
                print("Caught exception while getting reddit data:")
                print(e)
                print("Sleeping for 15 seconds.")
                time.sleep(15)


    def process_content(self, thing_type, thing, seen, reddit_instance):
        if thing.id in seen:
            return  # already reached up to here before
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
                return
            seen.add(thing.id)
            return
        if reddit_instance.has_replied(thing):
            print("We've replied to", thing_type, thing.id, "before!")
            if thing.id != cur_id:
                print("thing id changed, has replied")
                return
            seen.add(thing.id)
            return  # we reached here in a past instance of this bot

        if len(found) > 300:
            comments = ["Too many maps.\n\n" + self.formatter.footer]
            print("thing:", thing.id, "too many maps.")
            if thing.id != cur_id:
                print("thing id changed, too many maps")
                return
            reddit_instance.reply(thing, comments)
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
                return
            reddit_instance.reply(thing, comments)
            seen.add(thing.id)

    def run_scan_loop(self):
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

    def run_scan_stream(self):
        while True:
            comment_process = mp.Process(
                target=self.scan_content_stream,
                args=("comment",),
            )
            comment_process.start()

            submission_process = mp.Process(
                target=self.scan_content_stream,
                args=("submission",),
            )
            submission_process.start()

            mpc.wait([
                comment_process.sentinel,
                submission_process.sentinel
            ])

            print("Something went wrong - restarting processes.")
            submission_process.terminate()
            comment_process.terminate()
            print("Sleeping for 15 seconds.")
            time.sleep(15)


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
    bot.run_scan_stream()


if __name__ == '__main__':
    main()
