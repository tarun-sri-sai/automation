import argparse
import datetime as dt
import hashlib
import logging
import os
import shutil
import sys
import traceback
from pathlib import Path
from typing import Dict, Iterable, Tuple
from lib.logging_util import setup_logger


def list_dated_folders(backup_root: Path) -> list[Path]:
    folders = [entry for entry in backup_root.iterdir() if entry.is_dir()]
    return sorted(folders, key=lambda p: p.name)


def build_latest_index(
    source_folders: Iterable[Path]
) -> Dict[str, Tuple[str, Path]]:
    latest_by_name: Dict[str, Tuple[str, Path]] = {}

    for folder in source_folders:
        for entry in folder.iterdir():
            if not entry.is_file():
                continue
            latest_by_name[entry.name] = (folder.name, entry)

    return latest_by_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a synthetic full backup in the target dated folder by "
            "taking the latest dated-folder version of each exact filename."
        )
    )
    parser.add_argument(
        "-r",
        "--backup-root",
        help="Backup root containing dated folders (default: ../backup).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Preview actions without creating/copying files.",
    )
    return parser.parse_args()


def main() -> int:
    work_dir = os.path.dirname(__file__)
    script_file = os.path.basename(__file__)

    setup_logger(
        os.path.join(
            work_dir,
            "logs",
            os.path.splitext(script_file)[0] + ".log"
        )
    )
    logging.getLogger()

    try:
        args = parse_args()

        backup_root = Path(args.backup_root).expanduser().resolve()
        target_date = dt.date.today().strftime("%Y%m%d")

        if not backup_root.exists() or not backup_root.is_dir():
            logging.error(
                f"backup root not found or not a directory: {backup_root}"
            )
            return 2

        dated_folders = list_dated_folders(backup_root)
        if not dated_folders:
            logging.error(f"no dated folders found in {backup_root}")
            return 3

        target_folder = backup_root / target_date
        source_folders = [
            folder for folder in dated_folders if folder.name != target_date
        ]

        if not source_folders:
            logging.error(
                "no source dated folders found after excluding target date"
            )
            return 3

        latest_by_name = build_latest_index(source_folders)
        if not latest_by_name:
            logging.error("no regular files found in source dated folders")
            return 3

        for filename in sorted(latest_by_name):
            source_date, source_path = latest_by_name[filename]
            destination_path = target_folder / filename

            if destination_path.exists():
                continue

            logging.info(f"[copy]  {filename} <- {source_date}")
            if not args.dry_run:
                shutil.copy2(source_path, destination_path)

        logging.info("synthetic full backup finished successfully")
        return 0
    except Exception:
        logging.critical("failed to create synthetic full backup")
        logging.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
