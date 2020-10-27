from shutil import copy
import os

path = "./public"
path_backup = './backup'


def write_paths(path_file, content):
    f = open("." + path_file, "w")
    f.write(str(content))
    f.close()


def read_paths(path_file):
    f = open("." + path_file, "r")
    return f.read()


def copy_to_backup(created_files, updated_file, subdirs):
    for subdir in subdirs:
        new_path = path_backup + "/" + subdir
        if not os.path.exists(new_path):
            os.mkdir(new_path)

    for file in created_files:
        copy(path + "/" + file, path_backup + "/" + file)

    for up_file in updated_file:
        copy(path + "/" + up_file, path_backup + "/" + up_file)


def remove(files, dirs):
    for file in files:
        path_file = path_backup + "/" + file
        if os.path.exists(path_file):
            os.remove(path_file)
    for dir in dirs:
        path_folder = path_backup + "/" + dir
        if os.path.exists(path_folder):
            os.rmdir(path_folder)
