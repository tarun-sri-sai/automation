from fnmatch import fnmatch
from pathlib import Path


def is_excluded(root: Path, entry: Path, excludes: list[str]) -> bool:
    relative_path = entry.relative_to(root).as_posix()

    for pattern in excludes:
        if fnmatch(entry.name, pattern) or fnmatch(relative_path, pattern):
            return True

    return False
