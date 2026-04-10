import sys
import yaml
from pathlib import Path
from argparse import ArgumentParser
from lib.encryption import decrypt, encrypt


def walk_credentials(parent_path, recipient, pattern=None):
    if not pattern:
        pattern = "*"

    files = [f for f in Path(parent_path).rglob(pattern) if f.is_file()]
    for file in files:
        try:
            with open(file, "rb") as f:
                contents = decrypt(f.read(), recipient).decode("utf-8")

            data = yaml.safe_load(contents)
            sorted_contents = yaml.safe_dump(data, indent=4, sort_keys=True)

            if contents.replace("\r", "") != sorted_contents:
                print(f"{file} needs to be sorted")

                encrypt(sorted_contents, file, recipient)

        except AttributeError:
            print(f"{file} is not valid yaml", file=sys.stderr)
        except Exception as e:
            print(f"error while trying to sort {file} as yaml: {e}")


def main():
    parser = ArgumentParser(description="sort yaml credentials")
    parser.add_argument("directory", help="directory containing credential files")
    parser.add_argument("recipient", help="recipient to use for decryption and encryption")
    parser.add_argument("-f", "--filter", help="glob pattern to match files")

    args = parser.parse_args()

    walk_credentials(args.directory, args.recipient, args.filter)


if __name__ == '__main__':
    main()
