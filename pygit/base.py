import os
from . import data


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
            elif entry.is_dir(follow_symlinks=False):
                obj_type = "tree"
                oid = write_tree(full_path)
            obj_entries.append((entry.name, oid, obj_type))

    tree = "".join(
        f"{name} {oid} {obj_type}\n" for name, oid, obj_type in sorted(obj_entries)
    )
    return data.hash_object(tree.encode(), "tree")


def is_ignored(path):
    return ".pygit" in path.split("/")
