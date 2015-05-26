# BeatmapLinker
reddit bot, posts info about linked osu! beatmaps

At the time of writing, an instance of the bot is running at [/u/BeatmapLinker](https://www.reddit.com/user/BeatmapLinker). It would be preferable if another bot was not run in the same subreddits (osugame+osucommunity) if /u/BeatmapLinker is active. This will only cause confusion and frustration.

# Prerequisites

* A [reddit account](http://reddit.com/register) for your bot
* An [osu! API key](https://osu.ppy.sh/p/api) to get beatmap data
* Python 3 for the script
* Modules `praw` and `requests` for using the reddit and osu! APIs respectively.

Copy `config_example.ini` to `config.ini`, edit to your needs, and run the bot.  
The values used in the map and mapset templates are taken from the [JSON response](https://github.com/peppy/osu-api/wiki#response) of the osu! API, with a few slight changes for formatting.
