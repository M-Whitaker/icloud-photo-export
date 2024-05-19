#! /usr/bin/env python3
"""
A program that sets the creation date of an icloud export photo to the date the photo was taken.
"""

import os
import pathlib
from datetime import datetime as dt
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
import ffmpeg

from enum import Enum

register_heif_opener()

class FileType(Enum):
    IMAGE = 1
    VIDEO = 2

def get_file_type(path):
    """
    Get the type of file.
    """
    extension = pathlib.Path(path).suffix.lower()
    if extension in ['.jpg', '.jpeg', '.heic']:
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
            print(stream["tags"])
            return stream["tags"]
    raise Exception("No video stream found")

def set_creation_modify_date(path, date):
    """
    Set the creation and modification date of a file to the given date.
    """
    # TODO: Adjust for timesavings and zone
    os.utime(path, (date, date))

def main():
    """
    Program entry point.
    """
    paths = [r"32800492-9A12-48F3-8FDF-4B113C54F4FC.mp4"]

    for path in paths:
        date = None
        try:
            file_type = get_file_type(path)
            if file_type == FileType.IMAGE:
                meta = get_image_metadata(path)
                date = dt.strptime(meta['DateTime'], '%Y:%m:%d %H:%M:%S')
            elif file_type == FileType.VIDEO:
                meta = get_video_metadata(path)
        except Exception as e:
            print("Error reading metadata for: ", path)
            print(e)
            continue
        print("Fixing creation date for: ", path)
        print(meta)
        try:
            set_creation_modify_date(path, date.timestamp())
        except Exception as e:
            print("Error setting creation date for: ", path)
            print(e)
            continue

if __name__ == "__main__":
    main()
