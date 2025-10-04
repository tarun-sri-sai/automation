import os
import re
import shutil
from argparse import ArgumentParser


def convert_to_cap_snake_case(source_string):
    word_matches = re.findall(r'[a-zA-Z0-9]+', source_string)
    capitalized = [w.capitalize() for w in word_matches]
    return "_".join(capitalized)


def normalize(parent, dry_run):
    for item in os.listdir(parent):
        item_path = os.path.join(parent, item)
        try:
            if os.path.isfile(item_path):
                base_name, exts = item.split(".", 1)
                new_base_name = convert_to_cap_snake_case(base_name)
                new_name = f"{new_base_name}.{exts}"
            else:
                new_name = convert_to_cap_snake_case(item)
            new_path = os.path.join(parent, new_name)

            if new_path != item_path:
                conversion = f"{{{item} => {new_name}}}"
                conversion_path = os.path.join(parent, conversion)
                if dry_run:
                    print(f"Would rename {conversion_path}")
                else:
                    print(f"Renaming {conversion_path}")
                    shutil.move(item_path, new_path)

            if os.path.isdir(new_path):
                normalize(new_path, dry_run)
        except Exception as e:
            print(f"Failed to normalize {item_path}: {e}")


def main():
    parser = ArgumentParser(
        description="Normalizes files and directories recursively to Capitalized_Snake_Case"
    )
    parser.add_argument(
        "directory",
        help="Directory to be recursively normalized"
    )
    parser.add_argument(
        "-n", 
        "--dry-run", 
        help="Prints what would be renamed without renaming",
        dest="dry_run",
        action="store_true"
    )
    args = parser.parse_args()

    normalize(args.directory, args.dry_run)


if __name__ == '__main__':
    main()
