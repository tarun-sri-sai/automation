import hashlib
import json
import sys
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path


def file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)

    return h.hexdigest()


def is_excluded(root: Path, entry: Path, excludes: list[str]) -> bool:
    relative_path = entry.relative_to(root).as_posix()

    for pattern in excludes:
        if fnmatch(entry.name, pattern) or fnmatch(relative_path, pattern):
            return True

    return False


def walk(root: Path, path: Path, excludes: list[str]) -> dict:
    node = {
        "type": "directory",
        "name": path.name or str(path),
        "path": "." if path == root else path.relative_to(root).as_posix(),
        "children": [],
    }

    try:
        entries = sorted(path.iterdir(), key=lambda p: p.name)
    except PermissionError:
        print(f"permission denied: {path}", file=sys.stderr)
        sys.exit(1)

    for entry in entries:
        if is_excluded(root, entry, excludes):
            continue

        if entry.is_symlink():
            node["children"].append({
                "type": "symlink",
                "name": entry.name,
                "target": entry.readlink().as_posix(),
            })
        elif entry.is_dir():
            node["children"].append(walk(root, entry, excludes))
        elif entry.is_file():
            node["children"].append({
                "type": "file",
                "name": entry.name,
                "sha256": file_hash(entry),
            })
        else:
            node["children"].append({
                "type": "other",
                "name": entry.name,
            })

    return node


def build_tree(root: Path, excludes: list[str]) -> dict:
    if not root.is_dir():
        print(f"{root.name} is not a valid path", file=sys.stderr)
        sys.exit(1)

    root = root.resolve()

    return walk(root, root, excludes)


def main():
    parser = ArgumentParser(description="serialize a directory")
    parser.add_argument(
        "path",
        help="path to the directory to serialize"
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        help="exclude files or directories using glob pattern (repeatable)",
    )

    args = parser.parse_args()

    path = Path(args.path) or Path(".")
    output = json.dumps(build_tree(path, args.exclude))
    print(output)


if __name__ == "__main__":
    main()
