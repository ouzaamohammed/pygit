import os
import hashlib

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


# set the last commit's object id in .pygit/HEAD
def update_ref(ref, oid):
    ref_path = f"{git_dir}/{ref}"
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(oid)


def get_ref(ref):
    ref_path = f"{git_dir}/{ref}"
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            return f.read().strip()


def iter_refs():
    refs = ["HEAD"]
    for root, _, filenames in os.walk(f"{git_dir}/refs/"):
        root = os.path.relpath(root, git_dir)
        refs.extend(f"{root}/{filename}" for filename in filenames)

    for refname in refs:
        yield refname, get_ref(refname)
