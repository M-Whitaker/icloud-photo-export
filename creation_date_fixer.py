#! /usr/bin/env python3
"""
A program that sets the creation date of an icloud export photo to the date the photo was taken.
"""

import os
import pathlib
import argparse
from datetime import datetime as dt
from datetime import date as Date
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
import pillow_avif # pylint: disable=unused-import
import ffmpeg

from enum import Enum
from typing import Optional

DEBUG = False

register_heif_opener()

class FileType(Enum):
    IMAGE = 1
    VIDEO = 2

def get_file_type(path):
    """
    Get the type of file.
    """
    extension = pathlib.Path(path).suffix.lower()
    if extension in ['.jpg', '.jpeg', '.png', '.heic', '.avif']:
        return FileType.IMAGE
    elif extension in ['.mp4', '.mov']:
        return FileType.VIDEO
    else:
        raise Exception("File type not supported")

def get_image_metadata(path):
    """
    Get additional metadata from an image file.
    """
    image = Image.open(path)
    exif_data = image.getexif()
    metadata = {}
    for tag_id in exif_data:
        tagname = TAGS.get(tag_id, tag_id)
        value = exif_data.get(tag_id)
        metadata[tagname] = value
    return metadata

def get_video_metadata(path):
    streams = ffmpeg.probe(path)["streams"]
    for stream in streams:
        if stream["codec_type"] == "video":
            return stream["tags"]
    raise Exception("No video stream found")

def set_creation_modify_date(path, date):
    """
    Set the creation and modification date of a file to the given date.
    """
    os.utime(path, (date, date))

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Set the creation date of an icloud export photo to the date the photo was taken.")
    parser.add_argument("path", type=str, help="The path to the file.")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually set the creation date.")
    parser.add_argument("--debug", action="store_true", help="Print debug information.")
    return parser.parse_args()

def get_all_files_in_dir(path):
    """
    Get all files in a directory.
    """
    files = []
    for root, dirnames, filenames in os.walk(path):
        filenames = [f for f in filenames if not is_hidden_item(f)]
        dirnames[:] = [d for d in dirnames if not is_hidden_item(d)]

        for filename in filenames:
            path = os.path.join(root, filename)
            files.append(path)
    return files

def is_hidden_item(item):
    """
    Check if an item is hidden.
    """
    hidden = item.startswith(".")
    if DEBUG and hidden:
        print("Ignoring hidden item:", item)
    return hidden

def main():
    """
    Program entry point.
    """
    args = parse_args()
    
    if args.debug:
        global DEBUG
        DEBUG = True
    
    paths = get_all_files_in_dir(args.path)

    for path in paths:
        date: Optional[Date] = None
        try:
            file_type = get_file_type(path)
            if file_type == FileType.IMAGE:
                meta = get_image_metadata(path)
                date = dt.strptime(meta['DateTime'], '%Y:%m:%d %H:%M:%S')
            elif file_type == FileType.VIDEO:
                meta = get_video_metadata(path)
                date = dt.strptime(meta['creation_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception as e:
            print("Error reading metadata for:", path)
            print(e)
            continue
        print("Fixing creation date for:", path)
        print(meta)
        try:
            if date:
                if not args.dry_run:
                    set_creation_modify_date(path, date.timestamp())
                else:
                    print("Would set creation date to:", date)
            else:
                raise Exception("No date found")
        except Exception as e:
            print("Error setting creation date for: ", path)
            print(e)
            continue

if __name__ == "__main__":
    main()
