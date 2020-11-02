import os
import logging
import errno
import os.path as osp
from tensorflow.keras.utils import get_file
from typing import List

from graphgallery import is_listlike


def download_file(raw_paths: List[str],
                  urls: List[str]) -> None:

    last_except = None
    for filename, url in zip(raw_paths, urls):
        try:
            get_file(filename, origin=url)
        except Exception as e:
            last_except = e

    if last_except is not None:
        raise last_except


def files_exist(files: List[str]) -> bool:
    if is_listlike(files):
        return len(files) != 0 and all([osp.exists(f) for f in files])
    else:
        return osp.exists(files)


def makedirs(path: str) -> None:
    try:
        os.makedirs(osp.expanduser(osp.normpath(path)))
    except OSError as e:
        if e.errno != errno.EEXIST and osp.isdir(path):
            raise e


def makedirs_from_filename(filename: str, verbose: bool = True) -> None:
    file_dir = osp.split(osp.realpath(filename))[0]
    if not osp.exists(file_dir):
        makedirs(file_dir)
        if verbose:
            logging.log(logging.WARNING,
                        f"Creating a folder in {filename}.")
