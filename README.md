# auto_timelapse_script

Script for automatically downloading a list of videos, speeding them up, and concatenating them.    
Uses multithreading with youtube_dl and ffmpeg-python to download and speed up a list of videos all at once. Then, it uses ffmpeg to combine them all into one timelapse.

Made for https://cmpc.live


## Installation

You can use pip!    
```shell
python -m pip install cmpc-timelapse
```
Or just clone the repo.

## Usage

When installed using pip:    
As a python module    
```shell
python -m auto_timelapse
```
Or as a console script   
```shell
cmpc-timelapse
```

To use, create a file `vods.txt` with a list of youtube-dl compatible video URL's separated by newlines. Then, run in the same folder.    
Has a number of command line options, including `-h`, `--help`. Might add runtime input support.
