#!/usr/bin/env python


"""Script for automatically downloading a list of videos, speeding them up, and concatenating them.

Usage and options: see -h/--help

Files (configurable):
    vods.txt -- input list of video URL's, separated by newlines
    downloads/ -- folder which files will be downloaded to
"""


import re
import sys
import argparse
import concurrent.futures
from pathlib import Path

import youtube_dl as youtube_yl  # youtube yownloader
import ffmpeg


__version__ = '0.9.0'


# TODO: command-line argument support
# TODO: - option to turn off logging for youtube_dl and ffmpeg
# TODO: handle vod list input through input() after running
# TODO: option to disable multithreading or use a batch mode for large lists
# TODO: ffmpeg --enable-nvenc option
# TODO: function to get list of videos from option like youtube channel, maybe with time conditions


YOUTUBE_DL_DEFAULT_OUTTMPL = '%(title)s-%(id)s.%(ext)s'


# command line interface
parser = argparse.ArgumentParser(description='Script for automatically downloading a list of videos, speeding them up, '
                                             'and concatenating them.',
                                 usage='%(prog)s [-h] [--version] [OPTIONS] [VIDEO_URLS ...]')
parser.add_argument('--version', action='version', version=__version__)

parser.add_argument('video_urls', nargs='*', default=[])

parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help='show output from youtube-dl and ffmpeg')
parser.add_argument('-f', '--file', default='vods.txt', dest='vods_list_file_path',
                    help="path to file with list of video URL's, used if they are not given as arguments")
parser.add_argument('-o', '--out-folder', '--output', default='downloads', dest='out_folder',
                    help="folder to download to, default: '%(default)s'")
parser.add_argument('--overwrite', action='store_true', dest='clear_out_folder',
                    help='delete any and all files in the output folder before starting')
parser.add_argument('--no-clear', action='store_true', dest='no_clear',
                    help="Don't try to clear the out folder before starting. Allows resuming downloads, "
                    'but may mess up concatenation.')
parser.add_argument('-b', '--prefer-best-quality', action='store_true', dest='prefer_best_quality',
                    help='720p or lower will be used unless this option is selected, warning: may break concat')
parser.add_argument('-s', '--speed', type=int, default=1000, dest='speed',
                    help='multiplier for speeding up the video for ffmpeg, default: %(default)s')
parser.add_argument('-n', '--output-timelapse-name', default='_timelapse.mp4', dest='output_timelapse_filename',
                    help='name of final output, default: %(default)s, note:should include file extension, for ffmpeg')
parser.add_argument('-kt', '--keep-timelapse-parts', action='store_true', dest='keep_timelapse_parts',
                    help='individual sped up videos will be deleted unless this option is selected')
parser.add_argument('-ko', '--keep-original-parts', action='store_true', dest='keep_original_parts',
                    help='individual full length videos will be deleted unless this option is selected')

args = parser.parse_args()

# TODO: make this option work
# keep_full_length_versions = False


def clear_folder(out_folder, subfolders=('originals', 'speedup')):
    """Clear files in the given folder.

    Args:
        out_folder -- folder to clear files in
        subfolders -- folders within out_folder to also clear

    Folders in out_folder that are not included in subfolders will be ignored.
    Subfolders will be cleared but not deleted.
    If there are folders within the given subfolders, it may raise a PermissionError.
    """
    for subfolder in subfolders:
        subfolder = Path(out_folder) / subfolder
        if subfolder.is_dir():
            for file in subfolder.iterdir():
                # delete file
                file.unlink()

    for entry in Path(out_folder).iterdir():
        if not entry.is_dir():
            entry.unlink()


def out_folder_empty(out_folder=args.out_folder, overwrite=args.clear_out_folder):
    """Check whether the output folder is empty, and clear it if applicable.

    Args:
        overwrite -- whether or not to delete files in the folder if there are any
    Returns True if the folder doesn't exist or is empty.
    Returns False if the folder exists and contains files, unless overwrite is True, in which case it will
    delete all files in the folder and return True.
    """
    try:
        out_folder_contents = Path(out_folder).iterdir()
    except FileNotFoundError:
        return True
    else:
        if overwrite:
            print(f"Clearing downloads folder '{out_folder}'..")
            clear_folder(out_folder)
            return True
        else:
            return not out_folder_contents


def vods_list_from_file(path=args.vods_list_file_path):
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
        sys.exit(2)
    else:
        vods_list = list(set(vods_list))
        return vods_list


def download_and_speed_up(vods_list, out_folder=args.out_folder, prefer_best_quality=args.prefer_best_quality):
    """Download videos from a list of URL's using youtube-dl, and speed them up using ffmpeg.

    Downloads videos then automatically invokes the speed_up function on their filepath.
    If an invalid URL is given, it and all URL's after it in the list will be skipped. An error message will also
    be printed.

    Args:
        vods_list -- a list of youtube-dl compatible video URL's. May contain only one element, but must be a list
    """
    ydl_args = {
        # 'quiet': not args.verbose,
        'outtmpl': f'/{out_folder}/originals/{YOUTUBE_DL_DEFAULT_OUTTMPL}',
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


def speed_up(video_download, speed=args.speed):
    """Speeds up a video using ffmpeg. Works as a youtube_dl progress hook.

    The original video will be deleted. The speed multiplier is the 'speed' constant.

    Args:
        video_download -- dict with a 'status' key and a 'filename' key.
    """
    if not video_download['status'] == 'finished':
        return
    # filename, file_extension = os.path.splitext(video_download['filename'])
    # filename_no_extension = video_download['filename'][:-len(file_extension)]
    filename = Path(video_download['filename'])
    out_name = filename.with_stem(filename.stem + f'-{speed}x').name
    out_filename = filename.parents[1] / 'speedup' / out_name

    stream = ffmpeg.input(str(filename))
    stream = ffmpeg.setpts(stream, f'(1/{speed})*PTS')
    stream = ffmpeg.output(stream, str(out_filename))
    # if not args.verbose:
    #     stream = stream.global_args('-hide_banner')
    #     # stream = stream.global_args('-loglevel', 'warning')
    ffmpeg.run(stream)

    if not args.keep_original_parts:
        filename.unlink()


def combine_videos_in(
        folder=args.out_folder,
        subfolder='/speedup/',
        out_filename=args.output_timelapse_filename,
        keep_parts=args.keep_timelapse_parts
):
    """Combine videos in a folder into a single video using the ffmpeg concatenation demuxer.

    Original videos will be removed if keep_timelapse_parts is False.

    Args:
        folder -- the folder to combine videos in
    """
    folder_path = Path(folder)
    subfolder_path = folder_path / subfolder
    videos = subfolder_path.iterdir()
    parts_file_path = folder_path / '_parts.txt'

    with open(parts_file_path, 'w', encoding='utf-8') as parts_file:
        parts_file.writelines([f"file '{folder_path.joinpath(video)}'\n" for video in videos])

    stream = ffmpeg.input(parts_file_path, format='concat', safe=0)
    stream = ffmpeg.output(stream, folder_path.joinpath(out_filename), c='copy')
    # if not args.verbose:
    #     stream = stream.global_args('-hide_banner')
    #     # stream = stream.global_args('-loglevel', 'warning')
    ffmpeg.run(stream)

    if not keep_parts:
        parts_file_path.unlink()
        for video in videos:
            folder_path.joinpath(video).unlink()


def main():
    """Execute the script.

    First calls out_folder_empty and exits if result is False after printing an error message.
    Then uses threading to download videos got from the vod_list_from_file function, using the download_and_speed_up
    function.
    Finally combines the downloaded videos using the combine_videos_in function.
    """
    if not args.no_clear:
        if not out_folder_empty():
            print(f"The output folder '{args.out_folder}' contains files, please clear it or change the output folder.")
            sys.exit(1)

    if not args.video_urls:
        vods_list = vods_list_from_file()
    else:
        vods_list = args.video_urls
    print('Downloading and speeding up videos now with multithreading. You may see strange overlapping outputs.')
    with concurrent.futures.ThreadPoolExecutor() as threads:
        threads.map(download_and_speed_up, [[vod] for vod in vods_list])
    print('Downloading finished, combining videos.')
    combine_videos_in(args.out_folder)

    print('Done.')


if __name__ == '__main__':
    main()
