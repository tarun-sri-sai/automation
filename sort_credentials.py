import sys
import yaml
import warnings
from pathlib import Path
from argparse import ArgumentParser
from lib.encryption import decrypt, encrypt, read_password

warnings.filterwarnings("ignore")


def walk_credentials(parent_path, password, pattern=None):
    if not pattern:
        pattern = "*"

    files = [f for f in Path(parent_path).rglob(pattern) if f.is_file()]
    for file in files:
        try:
            with open(file, "rb") as f:
                contents = decrypt(f.read(), password)

            data = yaml.safe_load(contents)
            sorted_contents = yaml.safe_dump(data, sort_keys=True)

            if contents.replace("\r", "") != sorted_contents:
                print(f"{file} needs to be sorted")

                with open(file, "wb") as f:
                    f.write(encrypt(sorted_contents, password))

        except AttributeError:
            print(f"{file} is not valid yaml", file=sys.stderr)
        except Exception as e:
            print(f"error while trying to sort {file} as yaml: {e}")


def main():
    parser = ArgumentParser(description="sort yaml credentials")
    parser.add_argument("directory", help="directory containing credential files")
    parser.add_argument("-f", "--filter", help="glob pattern to match files")

    args = parser.parse_args()

    password = read_password("enter password: ")

    walk_credentials(args.directory, password, args.filter)


if __name__ == '__main__':
    main()
