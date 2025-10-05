import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="pygit", description="version control system cli"
    )
    parser.add_argument("init")
    args = parser.parse_args()
    print(args.init)
