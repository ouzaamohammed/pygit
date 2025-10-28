import subprocess

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp

from . import data


def compare_tree(*trees):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)


def diff_trees(tree_from, tree_to):
    output = b""
    for path, object_from, object_to in compare_tree(tree_from, tree_to):
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
