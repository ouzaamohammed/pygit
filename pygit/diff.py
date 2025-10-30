import subprocess

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp

from . import data


def compare_trees(*trees):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)


def diff_trees(tree_from, tree_to):
    output = b""
    for path, object_from, object_to in compare_trees(tree_from, tree_to):
        if object_from != object_to:
            output += diff_blobs(object_from, object_to, path)
    return output


def diff_blobs(object_from, object_to, path="blob"):
    with Temp() as file_from, Temp() as file_to:
        for oid, f in ((object_from, file_from), (object_to, file_to)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
            [
                "diff",
                "--unified",
                "--show-c-function",
                "--label",
                f"a/{path}",
                file_from.name,
                "--label",
                f"b/{path}",
                file_to.name,
            ],
            stdout=subprocess.PIPE,
        ) as proc:
            output, _ = proc.communicate()

        return output


def iter_changed_files(tree_from, tree_to):
    for path, object_from, object_to in compare_trees(tree_from, tree_to):
        if object_from != object_to:
            action = (
                "new file"
                if not object_from
                else "deleted" if not object_to else "modified"
            )
            yield path, action


def merge_trees(tree_base, tree_HEAD, tree_other):
    tree = {}
    for path, object_base, object_HEAD, object_other in compare_trees(
        tree_base, tree_HEAD, tree_other
    ):
        tree[path] = merge_blobs(object_base, object_HEAD, object_other)
    return tree


def merge_blobs(object_base, object_HEAD, object_other):
    with Temp() as file_base, Temp() as file_HEAD, Temp() as file_other:
        for oid, f in (
            (object_base, file_base),
            (object_HEAD, file_HEAD),
            (object_other, file_other),
        ):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
            [
                "diff3",
                "-m",
                "-L",
                "HEAD",
                file_HEAD.name,
                "-L",
                "BASE",
                file_base.name,
                "-L",
                "MERGE_HEAD",
                file_other.name,
            ],
            stdout=subprocess.PIPE,
        ) as proc:
            output, _ = proc.communicate()
            assert proc.returncode in (0, 1)

        return output
