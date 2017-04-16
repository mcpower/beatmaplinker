# BeatmapLinker
reddit bot, posts info about linked osu! beatmaps

At the time of writing, an instance of the bot is running at [/u/BeatmapLinker](https://www.reddit.com/user/BeatmapLinker). It would be preferable if another bot was not run in the same subreddits (osugame+osucommunity) if /u/BeatmapLinker is active. This will only cause confusion and frustration.

# Prerequisites

* A [reddit account](http://reddit.com/register) for your bot
* An [osu! API key](https://osu.ppy.sh/p/api) to get beatmap data
* Python 3 for the script
* Modules `praw` and `requests` for using the reddit and osu! APIs respectively.

# Configuration

Copy `config_example.ini` to `config.ini` and edit to your needs. Any option found in `config_default.ini` can be overridden in `config.ini`.

The only option not found in both the example and default configurations is `sep` under the `template` section. This defines the separator between the maps in a comment, which defaults to two new lines.

The map and mapset templates are `str.format`ted with the [JSON response](https://github.com/peppy/osu-api/wiki#response) from the osu! API. Some various replacements have been made:

* `difficultyrating` (star difficulty) has been converted into a float
* `hit_length` and `total_length` (length of beatmap) has been converted into a string in the form mm:ss
* all places where a Markdown character may appear are escaped

You can define your own replacements for things such as `mode` and `approved` with `replacements.ini`. An example is provided in `replacement_defaults.ini` which is used in the default configuration. Note that these are also `str.format`ted with the osu! API JSON response, like in the replacement `ar_display`.

# Default formatting

With the introduction of ranking status being available in comments, each status is formatted differently in the default configuration (which /u/BeatmapLinker uses). Most maps (approved and ranked) will be the usual bold, but the others are as below:

*  ❤ Loved ❤ 
* ***Qualified***
* **Approved**
* **Ranked**
* *Pending* (this seems to be unused)
* *WIP*
* Graveyard
