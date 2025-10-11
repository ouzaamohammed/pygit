import os
import hashlib

git_dir = ".pygit"


def init():
    os.makedirs(git_dir)
    os.makedirs(f"{git_dir}/objects")


def hash_object(data, obj_type="blob"):
    obj = obj_type.encode() + b"\x00" + data
    oid = hashlib.sha1(obj).hexdigest()
    with open(f"{git_dir}/objects/{oid}", "wb") as out:
        out.write(obj)
    return oid


def get_object(oid, expected="blob"):
    with open(f"{git_dir}/objects/{oid}", "rb") as f:
        obj = f.read()

    obj_type, _, content = obj.partition(b"\x00")
    obj_type = obj_type.decode()

    if expected is not None:
        assert obj_type == expected, f"Expect {expected}, got {obj_type}"
    return content
