
import re
import sys
import argparse
import warnings
from pathlib import Path
from lib.encryption import decrypt, read_password

# For warnings from cryptography
warnings.filterwarnings('ignore')


def find_files(directory, extension, recursive):
    path = Path(directory)
    if recursive:
        return path.rglob(f"*{extension}")
    else:
        return path.glob(f"*{extension}")


def decrypt_file(file_path, password):
    try:
        with open(file_path, 'r') as f:
            return decrypt(f.read(), password)
    except Exception as e:
        print(f"Error decrypting {file_path}: {e}", file=sys.stderr)
        return None


def search_in_content(file_path, content, pattern):
    matches = []
    try:
        for line in content.splitlines():
            if re.search(pattern, line):
                matches.append(line)
        return matches
    except Exception as e:
        print(f"Failed to find pattern in {file_path}: {e}", file=sys.stderr)
        return matches


def main():
    parser = argparse.ArgumentParser(
        description='Search for pattern in encrypted PGP files')
    parser.add_argument('directory', type=str, help='Directory to search')
    parser.add_argument('pattern', type=str, help='Pattern to search for')
    parser.add_argument('-e', '--extension', default='.asc',
                        help='File extension (default: .asc)')
    parser.add_argument('-r', '--recurse',
                        action='store_true', help='Search recursively')

    args = parser.parse_args()

    password = read_password("Enter password: ")

    files = find_files(args.directory, args.extension, args.recurse)
    for file_path in files:
        decrypted_content = decrypt_file(file_path, password)

        if decrypted_content:
            matches = search_in_content(
                file_path, decrypted_content, args.pattern)
            for match in matches:
                print(f"{file_path}: {match}")


if __name__ == "__main__":
    main()
