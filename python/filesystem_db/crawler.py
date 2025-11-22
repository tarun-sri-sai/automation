import os
import sys
import sqlite3
from argparse import ArgumentParser
from requests.structures import CaseInsensitiveDict

CHUNK_SIZE = 10000


def batched(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def read_directory_from_args():
    parser = ArgumentParser(
        prog="Directory Crawler",
        description="Builds a SQLite database for a directory structure"
    )
    parser.add_argument(
        "directory",
        help="Path to the directory you want to crawl"
    )
    args = parser.parse_args()

    directory_path = args.directory
    if not os.path.isdir(directory_path):
        raise ValueError(f"[{directory_path}] is not a valid directory")

    return directory_path


def get_all_files(parent_path):
    result = CaseInsensitiveDict()

    for root, _, files in os.walk(parent_path):
        for file in files:
            file_path = os.path.join(root, file)
            mt_time = os.path.getmtime(file_path)

            result[os.path.relpath(file_path, parent_path)] = int(mt_time)

    return dict(**result)


def main():
    try:
        directory_path = read_directory_from_args()
    except Exception as e:
        print(f"Failed to read directory from arguments: {e}")
        sys.exit(1)

    with sqlite3.connect("directory_tree.db") as conn:
        cursor = conn.cursor()

        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if not os.path.isdir(item_path):
                continue

            item_path = os.path.abspath(item_path)
            parent = os.path.basename(item_path)
            try:
                directory_tree = get_all_files(item_path)
            except Exception as e:
                print(f"Failed to crawl [{item_path}]: {e}")
                sys.exit(1)
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    parent VARCHAR(255),
                    path VARCHAR(65535), 
                    modified INTEGER,
                    PRIMARY KEY (parent, path)
                )
            ''')

            insert_stmt = ('''
                INSERT OR IGNORE INTO files (parent, path, modified)
                VALUES (?, ?, ?)
            ''')

            values = [(parent, p, m) for p, m in directory_tree.items()]
            for chunk in batched(values, CHUNK_SIZE):
                cursor.executemany(insert_stmt, chunk)
                conn.commit()


if __name__ == '__main__':
    main()
