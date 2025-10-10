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

    return parser.parse_args()


def init(args):
    data.init()
    print(f"initialized empty pygit directory in {os.getcwd()}/{data.git_dir}")
