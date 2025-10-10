import argparse
import os

from . import data


def main():
    args = parse_args()
    args.func(args)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="pygit", description="version control system cli"
    )

    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    return parser.parse_args()


def hash_object(args):
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def init(args):
    data.init()
    print(f"Initialized empty Pygit repository in {os.getcwd()}/{data.git_dir}")
