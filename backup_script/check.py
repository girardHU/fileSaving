import os
import functions as utils
import time


path = './public'
path_backup = './backup'


def compute_dir_index(path):
    files = []
    subdirs = []
    index = {}

    for root, dirs, filenames in os.walk(path):
        for subdir in dirs:
            subdirs.append(os.path.relpath(os.path.join(root, subdir), path))
        for f in filenames:
            files.append(os.path.relpath(os.path.join(root, f), path))

    for f in files:
        index[f] = os.path.getmtime(os.path.join(path, f))

    content = dict(files=files, subdirs=subdirs, index=index)
    return content


def compute_diff(dir_base, dir_cmp):
    data = {}
    data['deleted'] = list(set(dir_cmp['files']) - set(dir_base['files']))
    data['created'] = list(set(dir_base['files']) - set(dir_cmp['files']))
    data['updated'] = []
    data['deleted_dirs'] = list(set(dir_cmp['subdirs']) - set(dir_base['subdirs']))
    for f in set(dir_cmp['files']).intersection(set(dir_base['files'])):
        if dir_base['index'][f] != dir_cmp['index'][f]:
            data['updated'].append(f)

    return data


while True:
    content_main = compute_dir_index(path)
    content_backup = compute_dir_index(path_backup)
    subdirs = content_main["subdirs"]
    result = compute_diff(content_main, content_backup)

    created_file = result["created"]
    updated_file = result["updated"]
    deleted_file = result["deleted"]
    deleted_dir = result["deleted_dirs"]

    utils.copy_to_backup(created_file, updated_file, subdirs)
    utils.remove(deleted_file, deleted_dir)
    print("...")
    time.sleep(10)











