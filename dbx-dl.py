#!/usr/bin/env python3
"""Dropbox Downloader

Usage:
  dbx-dl.py download-recursive
  dbx-dl.py ls <path>
  dbx-dl.py (-h | --help)
  dbx-dl.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import dropbox
import dropbox.exceptions
import os.path

from docopt import docopt
from dropbox.files import FileMetadata, FolderMetadata
from configparser import ConfigParser
from pathlib import Path


class DropboxDownloader:

    def __init__(self):
        self._base_path = os.path.dirname(os.path.realpath(__file__))
        ini_settings = self._load_config()
        self._dbx = dropbox.Dropbox(ini_settings.get('main', 'api_key'))
        self._dl_dir = ini_settings.get('main', 'dl_dir')
        self._to_dl = str(ini_settings.get('main', 'to_dl')).split(',') or None

    def download_recursive(self, path=''):
        files_and_folders = self._dbx.files_list_folder(path)
        for f in files_and_folders.entries:
            if isinstance(f, FolderMetadata):
                if not self._to_dl or (self._to_dl and f.name in self._to_dl):
                    self.download_recursive(f.path_lower)
            elif isinstance(f, FileMetadata):
                self._download_file(f.path_lower)
            else:
                pass

    def ls(self, path):
        files_and_folders = self._dbx.files_list_folder(path)
        print('Listing path "{}"...'.format(path))
        fm = FolderMetadata()
        file_list = [{
            'id':         f.id,
            'name':       f.name,
            'path_lower': f.path_lower
        } for f in files_and_folders.entries]
        max_len_id = max(len(f['id']) for f in file_list)
        max_len_name = max(len(f['name']) for f in file_list)
        max_len_path_lower = max(len(f['path_lower']) for f in file_list)
        for f in file_list:
            line = '{:>{}} {:>{}} {:>{}}'.format(
                f['id'], max_len_id, f['name'], max_len_name, f['path_lower'], max_len_path_lower)
            print(line)

    def _download_file(self, path_lower):
        # dl file
        try:
            md, res = self._dbx.files_download(path_lower)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
        data = res.content

        # make sure dir exists
        fs_path = '{}/{}{}'.format(self._base_path, self._dl_dir, path_lower)
        fs_dir = os.path.dirname(fs_path)
        if not os.path.exists(fs_dir):
            print('Creating folder .{}'.format(os.path.dirname('{}{}'.format(self._dl_dir, path_lower))))
            Path(fs_dir).mkdir(parents=True)

        # write file
        if not os.path.exists(fs_path):
            print('Creating file ./{}{}'.format(self._dl_dir, path_lower))
            with open(fs_path, 'wb') as f:
                f.write(data)

    def _load_config(self):
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
        dd.download_recursive()
    elif arguments['ls']:
        dd.ls(arguments['<path>'])
