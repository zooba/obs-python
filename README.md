# obs-python

A Python bundle for OBS, designed to be easily added and integrated, as well as providing a richer API for script development.

Documentation is a TODO, as is most of the project. But here it is regardless!

# "Installing"

Unfortunately, given how OBS configuration works, there's no real installation for a script runtime. (I mean, there might be if I turned it into its own plugin... that might end up being a good idea anyway eventually...)

For now, here are the install steps (Windows 64-bit only):

1. Go to [the releases page](https://github.com/zooba/obs-python/releases) and select the most recent release
2. Download the `win64` artifact. It appears at the bottom of the run page.
3. Extract the ZIP file anywhere on your system, but remember where you put it.
4. In OBS, open "Tools" - "Scripts".
5. Select the "Python Settings" tab and browse to the directory you extracted.
6. Select the "Scripts" tab to add and use your scripts!

Note that the scripts in the [`samples`](https://github.com/zooba/obs-python/tree/master/samples) directory are not included in the download, so you will need to get them separately.

The path to Python is saved in your OBS profile, so switching profiles will reset that setting. Paths to scripts are saved in your scene collection, so switching that will reset scripts. Neither can be reliably shared with another machine unless you're certain you've installed things in the same location.

# "Uninstalling"

Nothing is going to go terribly wrong if you just delete the extracted folder. Make sure you've exited OBS first though.

# "Upgrading"

Repeat the installing steps and use the same folder when extracting.

# "Support"

Post in [Issues](https://github.com/zooba/obs-python/issues) here and wait. I'm not very good at responding to new issues on GitHub (so... many... notifications...), but I'll try, and other people may be able to share hacks or workarounds.

# Contributions

Very welcome! I reserve the right to reject anything for whatever reason I feel like, including "too trivial". If you're planning to contribute but don't even use OBS or Python, please find another project.

Interesting scripts are also most welcome. You can totally put your name on it, but once it's in the repo then it's fair game for fixes/tweaks/etc. from anyone.

I'm trying to keep this repo MIT licensed by avoiding copying anything from OBS itself that isn't part of its public interface. Depending on how [Google v. Oracle](https://en.wikipedia.org/wiki/Google_LLC_v._Oracle_America,_Inc.) goes, the final package and parts of the source may be relicensed to GPL.
