import re
import shutil
from argparse import ArgumentParser
from pathlib import Path
from lib.filesystem import is_excluded


def convert_to_kebab_case(source_string: str) -> str:
    word_matches: list[str] = re.findall(r'[a-zA-Z0-9\.]+', source_string)
    lowercase = [w.lower() for w in word_matches]
    return "-".join(lowercase)


def get_contents(
    root: Path,
    parent: Path,
    recursive: bool,
    exclude: list[str]
) -> dict[str, None | dict]:
    contents = {}
    for item in parent.iterdir():
        if is_excluded(root, item, exclude):
            continue

        if item.is_dir():
            contents[item.name] = (
                get_contents(root, item, recursive, exclude)
                if recursive
                else {}
            )
        else:
            contents[item.name] = None

    return contents


def allow_overwrite(new_path: Path) -> bool:
    if not new_path.exists():
        return True

    responses = {
        "y": True,
        "n": False,
        "": False
    }

    prompt = f"'{new_path}' exists. overwrite? [y/N]: "
    bad_input = "invalid input, please enter 'y' or 'n'"
    while True:
        response = input(prompt).strip().lower()
        if response in responses:
            return responses[response]
        else:
            print(bad_input)


def is_renamed(old_name: str, new_name: str) -> bool:
    return old_name.lower() != new_name.lower()


def try_normalize_path(path: Path, dry_run: bool) -> tuple[Path, str]:
    normalized = path.parent / convert_to_kebab_case(path.name)

    if dry_run:
        return path, normalized.name

    if is_renamed(path.name, normalized.name) and allow_overwrite(normalized):
        shutil.move(path, normalized)

    return normalized, normalized.name


def normalize_contents(
    parent: Path,
    contents: dict[str, None | dict],
    dry_run: bool,
    file_only: bool
) -> None:
    if file_only:
        new_parent, changed_name = parent, parent.name
    else:
        new_parent, changed_name = try_normalize_path(parent, dry_run)

    if is_renamed(parent.name, changed_name):
        print(f"[{parent.parent}]\n\t{parent.name} -> {changed_name}\n")

    normalized_files = []
    for key, value in contents.items():
        if value is not None:
            normalize_contents(new_parent / key, value, dry_run, file_only)

        else:
            _, changed_name = try_normalize_path(new_parent / key, dry_run)

            if is_renamed(key, changed_name):
                normalized_files.append((key, changed_name))

    if normalized_files:
        print(f"[{new_parent}]")
        for old_name, new_name in normalized_files:
            print(f"\t{old_name} -> {new_name}")
        print()


def normalize(
    parent: str,
    dry_run: bool,
    file_only: bool,
    recursive: bool,
    exclude: list[str]
) -> None:
    parent_path = Path(parent)

    contents = get_contents(parent_path, parent_path, recursive, exclude)
    normalize_contents(parent_path, contents, dry_run, file_only)


def main() -> None:
    parser = ArgumentParser(
        description="normalize files and directories to kebab-case"
    )
    parser.add_argument(
        "directory",
        help="directory to be normalized"
    )
    parser.add_argument(
        "-f",
        "--file-only",
        help="normalize files only, not directories",
        action="store_true"
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="normalize recursively",
        action="store_true"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        help="prints what would be renamed without renaming",
        action="store_true"
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        help="exclude files or directories using glob pattern (repeatable)",
    )

    args = parser.parse_args()

    try:
        normalize(
            args.directory,
            args.dry_run,
            args.file_only,
            args.recursive,
            args.exclude
        )
    except Exception as e:
        print(f"error: {e}")


if __name__ == '__main__':
    main()
