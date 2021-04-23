from dropbox.files import FileMetadata, FolderMetadata

from dropbox_utils import list_all_files


class DiskUsage:
    def __init__(self, dbx):
        self._dbx = dbx
        self.size = 0

    def du(self, path=''):
        """Get total size of given path by recursing through all subfolders, similar to linux `du` command."""
        self._du_sum_recursive(path)
        print('{}: {} bytes ({:0.2f} GB)'.format(path, self.size, self.size / 10 ** 9))

    def _du_sum_recursive(self, path):
        entries = list_all_files(self._dbx, path)
        for f in entries:
            if isinstance(f, FolderMetadata):
                self._du_sum_recursive(f.path_lower)
            elif isinstance(f, FileMetadata):
                self.size += f.size
            else:
                raise RuntimeError(
                    'Unexpected folder entry: {}\nExpected types: FolderMetadata, FileMetadata'.format(f))
