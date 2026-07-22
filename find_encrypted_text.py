
import re
import sys
import argparse
from collections.abc import Generator
from pathlib import Path
from lib.encryption.context import Context
from lib.encryption.gnupg.context import GnupgContext


def find_files(directory: Path, fil: str) -> Generator[Path, None, None]:
    if not fil:
        fil = "*"

    return directory.rglob(fil)


def decrypt_file(file_path, ctx: Context) -> str | None:
    try:
        with open(file_path, 'rb') as f:
            return ctx.decrypt(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error decrypting {file_path}: {e}", file=sys.stderr)
        return None


def search_in_content(
    file_path: Path, content: str, pattern: str
) -> list[str]:
    matches = []
    try:
        for line in content.splitlines():
            if re.search(pattern, line):
                matches.append(line)
        return matches
    except Exception as e:
        print(f"Failed to find pattern in {file_path}: {e}", file=sys.stderr)
        return matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Search for pattern in encrypted PGP files')

    parser.add_argument(
        "directory",
        type=Path,
        help="directory containing credential files"
    )
    parser.add_argument('pattern', type=str, help='Pattern to search for')
    parser.add_argument("-f", "--filter", help="glob pattern to match files")

    parser.add_argument(
        "-e",
        "--encryption-type",
        type=str,
        help="encryption used for the credentials"
    )
    parser.add_argument(
        "--gnupg-recipient",
        type=str,
        help="gnupg recipient to use for decryption and encryption"
    )

    ctx = None
    if args.encryption_type == "gnupg":
        ctx = GnupgContext(args.gnupg_recipient)
    else:
        raise ValueError(f"unsupported encryption type {args.encryption_type}")

    args = parser.parse_args()

    files = find_files(args.directory, args.filter)
    for file_path in files:
        decrypted_content = decrypt_file(file_path, ctx)
        if decrypted_content:
            matches = search_in_content(
                file_path, decrypted_content, args.pattern
            )
            for match in matches:
                print(f"{file_path}: {match}")


if __name__ == "__main__":
    main()
