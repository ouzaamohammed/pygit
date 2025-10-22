import os
import itertools
import operator

from . import data
from collections import namedtuple


def write_tree(directory="."):
    obj_entries = []
    with os.scandir(directory) as entries:
        for entry in entries:
            full_path = f"{directory}/{entry.name}"
            if is_ignored(full_path):
                continue

            if entry.is_file(follow_symlinks=False):
                obj_type = "blob"
                with open(full_path, "rb") as f:
                    oid = data.hash_object(f.read())
                    obj_entries.append((entry.name, oid, obj_type))
            elif entry.is_dir(follow_symlinks=False):
                obj_type = "tree"
                oid = write_tree(full_path)
                obj_entries.append((entry.name, oid, obj_type))

    tree = "".join(
        f"{obj_type} {oid} {name}\n" for name, oid, obj_type in sorted(obj_entries)
    )
    return data.hash_object(tree.encode(), "tree")


def is_ignored(path):
    return ".pygit" in path.split("/")


def _iter_tree_entries(oid):
    if not oid:
        return
    tree = data.get_object(oid, "tree")
    for entry in tree.decode().splitlines():
        obj_type, oid, name = entry.split(" ", 2)
        yield obj_type, oid, name


def get_tree(oid, base_path=""):
    result = {}
    for obj_type, oid, name in _iter_tree_entries(oid):
        assert "/" not in name
        assert name not in ("..", ".")
        path = base_path + name
        if obj_type == "blob":
            result[path] = oid
        elif obj_type == "tree":
            result.update(get_tree(oid, f"{path}/"))
        else:
            assert False, f"Unknown tree entry {obj_type}"
    return result


def _empty_current_directory():
    for root, dirnames, filenames in os.walk(".", topdown=False):
        for filename in filenames:
            path = os.path.relpath(f"{root}/{filename}")
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(f"{root}/{dirname}")
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                # Deletion might fail if the directory contains ignored files,
                # so it's OK
                pass


def read_tree(tree_oid):
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path="./").items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid))


def commit(message):
    commit = f"tree {write_tree()}\n"

    HEAD = data.get_HEAD()
    if HEAD:
        commit += f"parent {HEAD}\n"
    commit += "\n"
    commit += f"{message}\n"

    oid = data.hash_object(commit.encode(), "commit")
    data.set_HEAD(oid)
    return oid


Commit = namedtuple("Commit", ["tree", "parent", "message"])


def get_commit(oid):
    parent = None
    tree = None
    commit = data.get_object(oid, "commit").decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
        else:
            assert False, f"unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parent=parent, message=message)
