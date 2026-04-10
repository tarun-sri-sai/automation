import argparse
import difflib
import sys

from git import Repo
from git.exc import BadName
from git.objects import Blob

from lib.encryption import decrypt


def resolve_diff_commits(repo, revspec):
    if len(revspec) == 2:
        return revspec[0], revspec[1]

    if len(revspec) == 1:
        spec = revspec[0]

        if ".." in spec:
            if "..." in spec:
                left, right = spec.split("...")
                merge_base = repo.git.merge_base(left, right).strip()
                return merge_base, right
            else:
                left, right = spec.split("..")
                return left, right
        else:
            return spec, None

    raise ValueError("invalid revision specification")


def get_file_contents(repo, commit, path):
    if commit is None:
        try:
            with open(path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    try:
        obj = repo.commit(commit).tree / path
        if isinstance(obj, Blob):
            return obj.data_stream.read()
    except (KeyError, BadName):
        return None

    return None


def main():
    parser = argparse.ArgumentParser(
        description="decrypt a file at two git revisions and show unified diff"
    )

    parser.add_argument(
        "-r",
        "--recipient",
        required=True,
        type=str,
        help="recipient to use for decryption"
    )

    parser.add_argument(
        "revisions",
        nargs="+",
        help="revision spec (same formats supported by git diff)"
    )
    parser.add_argument(
        "--",
        dest="dashdash",
        action="store_true",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "path",
        help="Path to encrypted file"
    )

    args = parser.parse_args()

    if len(args.revisions) < 1:
        print("fatal: must provide at least one revision spec", file=sys.stderr)
        sys.exit(1)

    repo = Repo(search_parent_directories=True)

    try:
        left_rev, right_rev = resolve_diff_commits(repo, args.revisions)
    except ValueError as e:
        print(f"fatal: {e}", file=sys.stderr)
        sys.exit(1)

    encrypted_left = get_file_contents(repo, left_rev, args.path)
    encrypted_right = get_file_contents(repo, right_rev, args.path)

    recipient = args.recipient

    decrypted_left = (
        decrypt(encrypted_left, recipient).decode("utf-8").replace("\r\n", "\n")
        if encrypted_left is not None else ""
    )
    decrypted_right = (
        decrypt(encrypted_right, recipient).decode("utf-8").replace("\r\n", "\n")
        if encrypted_right is not None else ""
    )

    left_label = left_rev or "WORKING_TREE"
    right_label = right_rev or "WORKING_TREE"

    diff = difflib.unified_diff(
        decrypted_left.splitlines(keepends=True),
        decrypted_right.splitlines(keepends=True),
        fromfile=f"{args.path}@{left_label}",
        tofile=f"{args.path}@{right_label}",
    )

    for line in diff:
        print(line.replace("\n", ""))


if __name__ == "__main__":
    main()
