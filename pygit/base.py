import os
import itertools
import operator
import string

from . import data
from . import diff

from collections import deque, namedtuple


def init():
    data.init()
    data.update_ref("HEAD", data.ref_value(symbolic=True, value="refs/heads/master"))


def write_tree(directory="."):
    # Index is flat, we need it as a tree of dicts
    index_as_tree = {}
    with data.get_index() as index:
        for path, oid in index.items():
            path = path.split("/")
            dirpath, filename = path[:-1], path[-1]

            current = index_as_tree
            # Find the dict for the directory of this file
            for dirname in dirpath:
                current = current.setdefault(dirname, {})
            current[filename] = oid

    def write_tree_recursive(tree_dict):
        entries = []
        for name, value in tree_dict.items():
            if type(value) is dict:
                obj_type = "tree"
                oid = write_tree_recursive(value)
            else:
                obj_type = "blob"
                oid = value
            entries.append((name, oid, obj_type))

        tree = "".join(
            f"{obj_type} {oid} {name}\n" for name, oid, obj_type in sorted(entries)
        )
        return data.hash_object(tree.encode(), "tree")

    return write_tree_recursive(index_as_tree)


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


def read_tree(tree_oid, update_working=False):
    with data.get_index() as index:
        index.clear()
        index.update(get_tree(tree_oid))

        if update_working:
            _checkout_index(index)


def read_tree_merged(t_base, t_HEAD, t_other, update_working=False):
    with data.get_index() as index:
        index.clear()
        index.update(
            diff.merge_trees(get_tree(t_base), get_tree(t_HEAD), get_tree(t_other))
        )

        if update_working:
            _checkout_index(index)


def _checkout_index(index):
    _empty_current_directory()
    for path, oid in index.items():
        os.makedirs(os.path.dirname(f"./{path}"), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid, "blob"))


def commit(message):
    commit = f"tree {write_tree()}\n"

    HEAD = data.get_ref("HEAD").value
    if HEAD:
        commit += f"parent {HEAD}\n"
    MERGE_HEAD = data.get_ref("MERGE_HEAD").value
    if MERGE_HEAD:
        commit += f"parent {MERGE_HEAD}\n"
        data.delete_ref("MERGE_HEAD", deref=False)

    commit += "\n"
    commit += f"{message}\n"

    oid = data.hash_object(commit.encode(), "commit")
    data.update_ref("HEAD", data.ref_value(symbolic=False, value=oid))
    return oid


Commit = namedtuple("Commit", ["tree", "parents", "message"])


def get_commit(oid):
    parents = []
    tree = None
    commit = data.get_object(oid, "commit").decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parents.append(value)
        else:
            assert False, f"unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parents=parents, message=message)


def checkout(name):
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree)

    HEAD = None
    if is_branch(name):
        HEAD = data.ref_value(symbolic=True, value=f"refs/heads/{name}")
    else:
        HEAD = data.ref_value(symbolic=False, value=oid)

    data.update_ref("HEAD", HEAD, deref=False)


def is_branch(name):
    return data.get_ref(f"refs/heads/{name}").value is not None


def create_tag(name, oid):
    data.update_ref(f"refs/tags/{name}", data.ref_value(symbolic=False, value=oid))


def get_oid(name):
    if name == "@":
        name = "HEAD"

    # name is ref
    refs_to_try = [f"{name}", f"refs/{name}", f"refs/tags/{name}", f"refs/heads/{name}"]
    for ref in refs_to_try:
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref).value

    # name is SHA1
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name

    assert False, f"Unknown name {name}"


def iter_commits_and_parents(oids):
    # N.B. Must yield the oid before acccessing it (to allow caller to fetch it if needed)
    oids = deque(oids)
    visited = set()

    while oids:
        oid = oids.popleft()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid

        commit = get_commit(oid)
        # Return first parent next
        oids.extendleft(commit.parents[:1])
        # Return other parents later
        oids.extend(commit.parents[1:])


def iter_objects_in_commits(oids):
    # N.B. Must yield the oid before acccessing it (to allow caller to fetch it
    # if needed)
    visited = set()

    def iter_objects_in_tree(oid):
        visited.add(oid)
        yield oid
        for obj_type, oid, _ in _iter_tree_entries(oid):
            if oid not in visited:
                if obj_type == "tree":
                    yield from iter_objects_in_tree(oid)
                else:
                    visited.add(oid)
                    yield oid

    for oid in iter_commits_and_parents(oids):
        yield oid
        commit = get_commit(oid)
        if commit.tree not in visited:
            yield from iter_objects_in_tree(commit.tree)


def create_branch(name, oid):
    data.update_ref(f"refs/heads/{name}", data.ref_value(symbolic=False, value=oid))


def get_branch_name():
    HEAD = data.get_ref("HEAD", deref=False)
    if not HEAD.symbolic:
        return None
    HEAD = HEAD.value
    assert HEAD.startswith("refs/heads")
    return os.path.relpath(HEAD, "refs/heads")


def iter_branch_names():
    for refname, _ in data.iter_refs("refs/heads"):
        yield os.path.relpath(refname, "refs/heads")


def reset(oid):
    data.update_ref("HEAD", data.ref_value(symbolic=False, value=oid))


def get_working_tree():
    result = {}
    for root, _, filenames in os.walk("."):
        for filename in filenames:
            path = os.path.relpath(f"{root}/{filename}")
            if is_ignored(path) or not os.path.isfile(path):
                continue
            with open(path, "rb") as f:
                result[path] = data.hash_object(f.read())
    return result


def merge(other):
    HEAD = data.get_ref("HEAD").value
    assert HEAD
    merge_base = get_merge_base(other, HEAD)
    c_other = get_commit(other)

    # Handle fast-forward merge
    if merge_base == HEAD:
        read_tree(c_other.tree)
        data.update_ref("HEAD", data.ref_value(symbolic=False, value=other))
        print("Fast-forward merge, no need to commit")
        return

    data.update_ref("MERGE_HEAD", data.ref_value(symbolic=False, value=other))

    c_base = get_commit(merge_base)
    c_HEAD = get_commit(HEAD)

    read_tree_merged(c_base.tree, c_HEAD.tree, c_other.tree)
    print("Merged in working tree\nPlease commit")


def get_merge_base(oid1, oid2):
    parents = set(iter_commits_and_parents({oid1}))

    for oid in iter_commits_and_parents({oid2}):
        if oid in parents:
            return oid


def is_ancestor_of(commit, maybe_ancestor):
    return maybe_ancestor in iter_commits_and_parents({commit})


def add(filenames):
    def add_file(filename):
        # Normalize path
        filename = os.path.relpath(filename)
        with open(filename, "rb") as f:
            oid = data.hash_object(f.read())
            index[filename] = oid

    def add_directory(dirname):
        for root, _, filenames in os.walk(dirname):
            for filename in filenames:
                # Normalize path
                path = os.path.relpath(f"{root}/{filename}")
                if is_ignored(path) or not os.path.isfile(path):
                    continue
                add_file(filename)

    with data.get_index() as index:
        for name in filenames:
            if os.path.isfile(name):
                add_file(name)
            elif os.path.isdir(name):
                add_directory(name)
