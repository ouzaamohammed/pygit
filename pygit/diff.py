from collections import defaultdict


def compare_tree(*trees):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)


def diff_trees(tree_from, tree_to):
    output = ""
    for path, object_from, object_to in compare_tree(tree_from, tree_to):
        if object_from != object_to:
            output += f"changed: {path}\n"
    return output
