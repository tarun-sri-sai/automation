import argparse
import difflib
import sys
from git import Repo
from pathlib import Path
from typing import Any
from lib.encryption import GnupgContext


def resolve_diff_commits(
    repo: Repo, revspec: list[str]
) -> tuple[str, str | None]:
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


def get_file_contents(repo: Repo, commit: str | None, path: str) -> Any:
    path = Path(path).absolute().relative_to(repo.working_tree_dir).as_posix()

    if commit is None:
        with open(Path(repo.working_tree_dir) / path, "rb") as f:
            return f.read()

    obj = repo.commit(commit).tree / path
    return obj.data_stream.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="decrypt a file at two git revisions and show unified diff"
    )

    parser.add_argument(
        "-e", "--encryption-type", type=str,
        help="encryption used for the credentials"
    )
    parser.add_argument(
        "--gnupg-recipient", type=str,
        help="gnupg recipient to use for decryption and encryption"
    )
    parser.add_argument(
        "-p", "--path", type=str, required=True,
        help="Path to encrypted file"
    )

    parser.add_argument(
        "revisions", nargs="+",
        help="revision spec (same formats supported by git diff)"
    )

    args = parser.parse_args()

    if len(args.revisions) < 1:
        print(
            "fatal: must provide at least one revision spec", file=sys.stderr
        )
        sys.exit(1)

    file_path = Path(args.path)
    if not file_path.is_file():
        print(f"fatal: {file_path} is not a file", file=sys.stderr)
        sys.exit(1)

    repo = Repo(file_path.parent, search_parent_directories=True)
    print(f"using git repository at {repo.working_tree_dir}", file=sys.stderr)

    left_rev, right_rev = resolve_diff_commits(repo, args.revisions)

    encrypted_left = get_file_contents(repo, left_rev, file_path)
    encrypted_right = get_file_contents(repo, right_rev, file_path)

    ctx = None
    if args.encryption_type == "gnupg":
        ctx = GnupgContext(args.gnupg_recipient)
    else:
        raise ValueError(f"unsupported encryption type {args.encryption_type}")

    decrypted_left = (
        ctx.decrypt(encrypted_left).decode("utf-8").replace("\r\n", "\n")
        if encrypted_left is not None else ""
    )
    decrypted_right = (
        ctx.decrypt(encrypted_right).decode("utf-8").replace("\r\n", "\n")
        if encrypted_right is not None else ""
    )

    left_label = left_rev or "WORKING_TREE"
    right_label = right_rev or "WORKING_TREE"

    diff = difflib.unified_diff(
        decrypted_left.splitlines(keepends=True),
        decrypted_right.splitlines(keepends=True),
        fromfile=f"{file_path}@{left_label}",
        tofile=f"{file_path}@{right_label}",
    )

    for line in diff:
        print(line.replace("\n", ""))


if __name__ == "__main__":
    main()
