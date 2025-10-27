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


def update_ref(ref, value, deref=True):
    ref = _get_ref_internal(ref, deref)[0]

    assert value.value
    if value.symbolic:
        value = f"ref: {value.value}"
    else:
        value = value.value

    ref_path = f"{git_dir}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(value)


def get_ref(ref, deref=True):
    return _get_ref_internal(ref, deref)[1]


def _get_ref_internal(ref, deref):
    ref_path = f"{git_dir}/{ref}"
    value = None
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()

    symbolic = bool(value) and value.startswith("ref: ")
    if symbolic:
        value = value.split(":", 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)

    return ref, ref_value(symbolic=symbolic, value=value)


def iter_refs(prefix="", deref=True):
    refs = ["HEAD"]
    for root, _, filenames in os.walk(f"{git_dir}/refs/"):
        root = os.path.relpath(root, git_dir)
        refs.extend(f"{root}/{filename}" for filename in filenames)

    for refname in refs:
        if not refname.startswith(prefix):
            continue
        yield refname, get_ref(refname, deref=deref)
