#!/usr/bin/env python3
"""Dropbox Downloader

Usage:
  dbx-dl.py download-recursive [<path>]
  dbx-dl.py du [<path>]
  dbx-dl.py ls [<path>]
  dbx-dl.py (-h | --help)
  dbx-dl.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import os.path
from configparser import ConfigParser
from queue import Queue

import dropbox
import dropbox.exceptions
from docopt import docopt
from dropbox.files import FolderMetadata, FileMetadata

from dropbox_downloader.DiskUsage import DiskUsage
from dropbox_downloader.DownloadWorker import DownloadWorker
from dropbox_downloader.Downloader import Downloader
from dropbox_utils import list_all_files


class DropboxDownloader:
    """Controlling class for console command."""

    def __init__(self):
        self._base_path = os.path.dirname(os.path.realpath(__file__))
        ini_settings = self._load_config()
        self._dbx = dropbox.Dropbox(ini_settings.get('main', 'api_key'))
        self._dl_dir = ini_settings.get('main', 'dl_dir')
        self._to_dl = str(ini_settings.get('main', 'to_dl')).split(',') or None

    def dl(self, path: str = ''):
        """Recursively download all files in given path, or entire dropbox if none given"""
        d = Downloader(self._base_path, self._dbx, self._dl_dir, self._to_dl)
        queue = Queue()

        entries = d.list_files_and_folders(path)
        n_files_and_folders = len(entries)
        n_threads = n_files_and_folders if n_files_and_folders < 8 else 8

        # Create 8 ListWorker threads
        for x in range(n_threads):
            worker = DownloadWorker(d, queue)
            # Setting daemon to True will let the main thread exit even though the workers are blocking
            worker.daemon = True
            worker.start()

        for f in entries:
            if isinstance(f, FolderMetadata):
                queue.put(f.path_lower)
            elif isinstance(f, FileMetadata):
                d.download_file(f)
            else:
                raise RuntimeError(
                    'Unexpected folder entry: {}\nExpected types: FolderMetadata, FileMetadata'.format(f))

        # Causes the main thread to wait for the queue to finish processing all the tasks
        queue.join()
        print('All files in {} downloaded'.format(path or 'your entire dropbox'))

    def du(self, path: str = ''):
        """Get disk usage (size) for path"""
        du = DiskUsage(self._dbx)
        du.du(path)

    def ls(self, path: str = ''):
        """Print contents of a given folder path in text columns"""
        entries = list_all_files(self._dbx, path)
        print('Listing path "{}"...'.format(path))
        file_list = [{
            'id': f.id,
            'name': f.name,
            'path_lower': f.path_lower
        } for f in entries]

        # get column sizes for formatting
        max_len_id = max(len(f['id']) for f in file_list)
        max_len_name = max(len(f['name']) for f in file_list)
        max_len_path_lower = max(len(f['path_lower']) for f in file_list)
        for f in file_list:
            print('{:>{}} {:>{}} {:>{}}'.format(
                f['id'], max_len_id, f['name'], max_len_name, f['path_lower'], max_len_path_lower))

    def _load_config(self) -> ConfigParser:
        """Load `dbx-dl.ini` config file

        :return: ConfigParser
        """
        # By using `allow_no_value=True` we are allowed to
        # write `--force` instead of `--force=true` below.
        config = ConfigParser(allow_no_value=True)
        with open('{}/dbx-dl.ini'.format(self._base_path)) as f:
            config.read_file(f)

        return config


if __name__ == '__main__':
    arguments = docopt(__doc__, version='Dropbox Downloader')
    dd = DropboxDownloader()
    if arguments['download-recursive']:
        dd.dl(arguments.get('<path>') or '')
    elif arguments.get('du'):
        dd.du(arguments.get('<path>') or '')
    elif arguments.get('ls'):
        dd.ls(arguments.get('<path>') or '')
