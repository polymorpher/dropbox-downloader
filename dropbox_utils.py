import dropbox
from dropbox.files import ListFolderResult


def list_all_files(db: dropbox.Dropbox, path: str):
    r = db.files_list_folder(path)
    ret = []

    def add(res: ListFolderResult):
        ret.extend(res.entries)

    add(r)
    while r.has_more:
        r = db.files_list_folder_continue(r.cursor)
        add(r)
    return ret
