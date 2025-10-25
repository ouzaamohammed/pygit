import os
import hashlib

from collections import namedtuple

git_dir = ".pygit"


def init():
    os.makedirs(git_dir)
    os.makedirs(f"{git_dir}/objects")


# Write binary data into file name that generated using sha-1 & return object id
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


ref_value = namedtuple("ref_value", ["symbolic", "value"])


# set the last commit's object id in .pygit/HEAD
def update_ref(ref, value):
    assert not value.symbolic
    ref_path = f"{git_dir}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(value.value)


def get_ref(ref):
    ref_path = f"{git_dir}/{ref}"
    value = None
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()

    if value and value.startswith("ref: "):
        return get_ref(value.split(":", 1)[1].strip())

    return ref_value(symbolic=False, value=value)


def iter_refs():
    refs = ["HEAD"]
    for root, _, filenames in os.walk(f"{git_dir}/refs/"):
        root = os.path.relpath(root, git_dir)
        refs.extend(f"{root}/{filename}" for filename in filenames)

    for refname in refs:
        yield refname, get_ref(refname)
