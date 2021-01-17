# auto_timelapse_script

Script for automatically downloading a list of videos, speeding them up, and concatenating them.
Uses multithreading with youtube_dl and ffmpeg-python to download and speed up a list of videos all at once. Then, it uses ffmpeg to combine them all into one timelapse.

Made for https://www.twitch.tv/controlmypc

## Usage

To use, create a file `vods.txt` with a list of youtube-dl compatible video URL's separated by newlines. Then, run in the same folder.
Has a number of options that can be modified as variables at the start of the program. Command line options support and maybe other methods will be added.
