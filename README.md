# BeatmapLinker
reddit bot, posts info about linked osu! beatmaps

At the time of writing, an instance of the bot is running at [/u/BeatmapLinker](https://www.reddit.com/user/BeatmapLinker). It would be preferable if another bot was not run in the same subreddits (osugame+osucommunity) if /u/BeatmapLinker is active. This will only cause confusion and frustration.

# Prerequisites

* A [reddit account](http://reddit.com/register) for your bot
* An [osu! API key](https://osu.ppy.sh/p/api) to get beatmap data
* Python 3 for the script
* Modules `praw` and `requests` for using the reddit and osu! APIs respectively.

Copy `config_example.ini` to `config.ini`, `template_extras_example.ini` to `template_extras.ini` edit to your needs, and run the bot.  
The values used in the map and mapset templates are taken from the [JSON response](https://github.com/peppy/osu-api/wiki#response) of the osu! API, with a few slight changes for formatting.

# Default formatting

With the introduction of ranking status being available in comments, each status is formatted differently in the default configuration (which /u/BeatmapLinker uses). Most maps (approved and ranked) will be the usual bold, but the others are as below:

* ***Qualified***
* **Approved**
* **Ranked**
* Pending
* WIP
* ~~Graveyard~~
