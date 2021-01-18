#!usr/env/bin python


"""Script for automatically downloading a list of videos, speeding them up, and concatenating them.

Files:
    vods.txt -- input list of video URL's, separated by newlines
    downloads/ -- folder which files will be downloaded to

Usage: cmpc-timelapse

Options (variables at start of file, better options system to follow):
    vods_list_file_path -- path to file with list of video URL's
    out_folder -- folder to download videos to, must be empty unless clear_out_folder is True
    clear_out_folder -- delete all files in out_folder
    prefer_best_quality -- videos will be downloaded in 720p or smaller unless this is True
    speed -- multiplier for speeding up videos
    output_timelapse_filename -- name for the concatenated version of all the sped up videos
    keep_timelapse_parts -- individual sped up videos are deleted unless this is True
"""


import re
import os
import sys
import concurrent.futures

import youtube_dl as youtube_yl  # youtube yownloader
import ffmpeg


__version__ = '0.6.8'


# TODO: command-line argument support
# TODO: - vod urls as a list of arguments
# TODO: - prefer 1080p option (720p default)
# TODO: - delete sped up vods and only keep concat version
# TODO: - option to overwrite output folder
# TODO: - option for how much to speed up video
# TODO: - option to keep audio in timelapse?
# TODO: - option to turn off logging for youtube_dl and ffmpeg
# TODO: handle vod list input through input() after running
# TODO: option to disable multithreading or use a batch mode for large lists
# TODO: refine function arguments, reduce use of 'constants'


YOUTUBE_DL_DEFAULT_OUTTMPL = '%(title)s-%(id)s.%(ext)s'

vods_list_file_path = 'vods.txt'
out_folder = 'downloads'
clear_out_folder = False
prefer_best_quality = False
# TODO: make this option work
# keep_full_length_versions = False
speed = 1000
output_timelapse_filename = '_timelapse.mp4'
keep_timelapse_parts = True


def out_folder_empty(overwrite=clear_out_folder):
    """Check whether the output folder is empty, and clear it if applicable.

    Args:
        overwrite -- whether or not to delete files in the folder if there are any
    Returns True if the folder doesn't exist or is empty.
    Returns False if the folder exists and contains files, unless overwrite is True, in which case it will
    delete all files in the folder and return True.
    """
    try:
        out_folder_contents = os.listdir(out_folder)
    except FileNotFoundError:
        return True
    else:
        if overwrite:
            print(f"Clearing downloads folder '{out_folder}'..")
            for file in out_folder_contents:
                os.remove(os.path.join(out_folder, file))
            return True
        else:
            return not out_folder_contents


def remove_duplicates(videos):
    """Remove duplicate items in a list and return it.

    Args:
        videos -- input list
    Returns the list with duplicate items removed, which may be identical to the original list if there were
    no duplicate items.
    """
    seen = set()
    unique_videos = []
    for video in videos:
        if video not in seen:
            unique_videos.append(video)
            seen.add(video)

    return unique_videos


def vods_list_from_file(path=vods_list_file_path):
    """Get a list of video URL's from a file.

    Prints an error message and exits the program if the file is not found.

    Args:
        path -- file path to a text file of newline-separated video URL's
    Returns a list of URL's with duplicates removed.
    """
    try:
        with open(path, 'r') as vods_list_file:
            vods_list = vods_list_file.read().splitlines()
    except FileNotFoundError:
        print(f"List of VODs to download '{path}' not found.")
        sys.exit()
    else:
        vods_list = remove_duplicates(vods_list)
        return vods_list


def download(vods_list):
    """Download videos from a list of URL's using youtube-dl, and speed them up using ffmpeg.

    Downloads videos then automatically invokes the speed_up function on their filepath.
    If an invalid URL is given, it and all URL's after it in the list will be skipped. An error message will also
    be printed.

    Args:
        vods_list -- a list of youtube-dl compatible video URL's. May contain only one element, but must be a list
    """
    ydl_args = {
        'outtmpl': f'/{out_folder}/{YOUTUBE_DL_DEFAULT_OUTTMPL}',
        'progress_hooks': [speed_up],
    }
    if not prefer_best_quality:
        ydl_args['format'] = 'best[height<=720]/best'

    try:
        with youtube_yl.YoutubeDL(ydl_args) as ydl:
            ydl.download(vods_list)
    except youtube_yl.utils.DownloadError as error:
        invalid_url = 'unknown'
        re_match = re.match(r"ERROR: '(.*)' is not a valid URL\.", error.args[0])
        if re_match:
            invalid_url = re_match.group(1)
        print(f'Invalid video URL, skipping. Invalid URL: {invalid_url}')


def speed_up(video_download):
    """Speeds up a video using ffmpeg. Works as a youtube_dl progress hook.

    The original video will be deleted. The speed multiplier is the 'speed' constant.

    Args:
        video_download -- dict with a 'status' key and a 'filename' key.
    """
    if not video_download['status'] == 'finished':
        return
    filename, file_extension = os.path.splitext(video_download['filename'])
    filename_no_extension = video_download['filename'][:-len(file_extension)]

    stream = ffmpeg.input(video_download['filename'])
    stream = ffmpeg.setpts(stream, f'(1/{speed})*PTS')
    stream = ffmpeg.output(stream, f"{filename_no_extension}-{speed}x{file_extension}")
    ffmpeg.run(stream)

    os.remove(video_download['filename'])


def combine_videos_in(folder=out_folder):
    """Combine videos in a folder into a single video using the ffmpeg concatenation demuxer.

    Original videos will be removed if keep_timelapse_parts is False.

    Args:
        folder -- the folder to combine videos in
    """
    videos = os.listdir(folder)
    parts_file_path = os.path.join(folder, '_parts.txt')

    with open(parts_file_path, 'w', encoding='utf-8') as parts_file:
        parts_file.writelines([f"file '{os.path.join(folder, video)}'\n" for video in videos])

    stream = ffmpeg.input(parts_file_path, format='concat', safe=0)
    stream = ffmpeg.output(stream, os.path.join(folder, output_timelapse_filename), c='copy')
    ffmpeg.run(stream)

    if not keep_timelapse_parts:
        os.remove(parts_file_path)
        for video in videos:
            os.remove(os.path.join(folder, video))


def main():
    """Execute the script.

    First calls out_folder_empty and exits if result is False after printing an error message.
    Then uses threading to download videos got from the vod_list_from_file function, using the download function.
    Finally combines the downloaded videos using the combine_videos_in function.
    """
    if not out_folder_empty():
        print(f"The output folder '{out_folder}' contains files, please clear it or change the output folder.")
        sys.exit()

    vods_list = vods_list_from_file()
    print('Downloading and speeding up videos now with multithreading. You may see strange overlapping outputs.')
    with concurrent.futures.ThreadPoolExecutor() as threads:
        threads.map(download, [[vod] for vod in vods_list])
    print('Downloading finished, combining videos.')
    combine_videos_in(out_folder)

    print('Done.')


if __name__ == '__main__':
    main()
