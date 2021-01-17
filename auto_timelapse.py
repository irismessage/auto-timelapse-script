#!usr/env/bin python

import sys

import youtube_dl
import ffmpeg

# TODO: command-line argument support
# TODO: - vod urls as a list of arguments
# TODO: - prefer 1080p option (720p default)
# TODO: - delete sped up vods and only keep concat version


YOUTUBE_DL_DEFAULT_OUTTMPL = '%(title)s-%(id)s.%(ext)s'

vods_list_file_path = 'vods.txt'
prefer_1080p = False


def vods_list_from_file(path=vods_list_file_path):
    try:
        with open(path, 'r') as vods_list_file:
            vods_list = vods_list_file.read().splitlines()
    except FileNotFoundError:
        print(f"List of VODs to download '{path}' not found.")
        sys.exit()
    else:
        return vods_list


def download(vods_list):
    ydl_args = {
        'outtmpl': f'/downloads/{YOUTUBE_DL_DEFAULT_OUTTMPL}',
    }
    if not prefer_1080p:
        ydl_args['format'] = 'best[height=720]'

    with youtube_dl.YoutubeDL(ydl_args) as ydl:
        ydl.download(vods_list)


def main():
    vods_list = vods_list_from_file()
    download(vods_list)


if __name__ == '__main__':
    main()
