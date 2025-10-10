import os
import hashlib

git_dir = ".pygit"


def init():
    os.makedirs(git_dir)
    os.makedirs(f"{git_dir}/objects")


def hash_object(data):
    oid = hashlib.sha1(data).hexdigest()
    with open(f"{git_dir}/objects/{oid}", "wb") as out:
        out.write(data)
    return oid


def get_object(oid):
    with open(f"{git_dir}/objects/{oid}", "rb") as f:
        return f.read()
