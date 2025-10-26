import os
import sys
import sqlite3
from argparse import ArgumentParser
import sys

CHUNK_SIZE = 10000
sys.stdout.reconfigure(encoding='utf-8')


def batched(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def read_args():
    parser = ArgumentParser(
        prog="Directory Cleanup",
        description=("Uses the DB built with crawler.py to cleanup duplicates "
                     "of files, only one file from the duplicates is kept")
    )
    parser.add_argument(
        "directory",
        help="Path to the directory you want to clean up"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="When set, only prints the files to delete, does not delete them"
    )
    args = parser.parse_args()

    directory_path = args.directory
    if not os.path.isdir(directory_path):
        raise ValueError(f"[{directory_path}] is not a valid directory")

    return directory_path, args.dry_run


def main():
    try:
        directory_path, dry_run = read_args()
    except Exception as e:
        print(f"Failed to read directory from arguments: {e}")
        sys.exit(1)
    directory_path = os.path.abspath(directory_path)

    with sqlite3.connect("directory_tree.db") as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                parent VARCHAR(255),
                path VARCHAR(65535), 
                modified INTEGER,
                PRIMARY KEY (parent, path)
            )
        ''')

        select_stmt = ('''
            WITH ranked_files AS (
                SELECT
                    parent,
                    path,
                    modified,
                    ROW_NUMBER() OVER (PARTITION BY path, modified ORDER BY parent ASC) AS rn,
                    COUNT(*) OVER (PARTITION BY path, modified) AS cnt
                FROM files
            )
            SELECT parent, path, modified
            FROM ranked_files
            WHERE rn < cnt
            ORDER BY path, parent;
        ''')

        cursor.execute(select_stmt)

        rows_to_delete = []
        for parent, path, _ in cursor.fetchall():
            rows_to_delete.append((parent, path))
            file_to_remove = os.path.join(directory_path, parent, path)
            print(file_to_remove)

            if not dry_run and os.path.isfile(file_to_remove):
                os.remove(file_to_remove)

        if not dry_run:
            delete_stmt = ('''
                DELETE FROM files WHERE
                parent = ? AND path = ?
            ''')
                        
            for chunk in batched(rows_to_delete, CHUNK_SIZE):
                cursor.executemany(delete_stmt, chunk)
                conn.commit()


if __name__ == '__main__':
    main()
