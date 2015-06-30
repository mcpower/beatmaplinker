import praw
from functools import reduce
import html


class Reddit:
    def __init__(self, username, password, user_agent, subreddit):
        self.r = praw.Reddit(user_agent=user_agent)
        self.r.login(username, password)
        self.subreddit = self.r.get_subreddit(subreddit)

        self.botname = username

    def has_replied(self, t):
        """Checks whether the bot has replied to a thing already.

        Apparently costly.
        Taken from http://reddit.com/r/redditdev/comments/1kxd1n/_/cbv4usl"""
        if isinstance(t, praw.objects.Comment):
            replies = self.r.get_submission(t.permalink).comments[0].replies
        elif isinstance(t, praw.objects.Submission):
            replies = t.comments
        else:
            raise Exception("{0} is an invalid thing type".format(type(t)))
        return any(reply.author.name == self.botname for reply in replies)

    def reply(self, thing, texts):
        """Post comment(s) replying to a thing.

        Takes in a list of comments to chain.
        """
        if thing.author.name == self.botname:
            print("Replying to self. Terminating.")
            return
        return reduce(lambda thing, text: self.reply_single(thing, text),
                      texts, thing)

    def reply_single(self, thing, text):
        """Post a comment replying to a thing."""
        print("""Replying to {c.author.name}, thing id {c.id}\n{text}\n"""
              .format(c=thing, text=text))

        if isinstance(thing, praw.objects.Comment):
            out = thing.reply(text)
        elif isinstance(thing, praw.objects.Submission):
            out = thing.add_comment(text)
        else:
            raise Exception("{0} is an invalid thing type".format(type(thing)))
        print("Replied!")
        return out

    def get_comments(self, limit):
        return self.subreddit.get_comments(limit=limit)

    def get_submissions(self, limit):
        return self.subreddit.get_new(limit=limit)


def get_html_from_thing(thing):
    """Returns the HTML content of a thing."""
    if isinstance(thing, praw.objects.Comment):
        out = thing.body_html
    elif isinstance(thing, praw.objects.Submission):
        out = thing.selftext_html
        if not out:
            return ""
    else:
        raise Exception("{0} is an invalid thing type".format(type(thing)))
    return html.unescape(out)
