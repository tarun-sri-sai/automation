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
    folders = [entry for entry in backup_root.iterdir()]
    return sorted(folders, key=lambda p: p.name)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def files_identical(a: Path, b: Path) -> bool:
    if a.stat().st_size != b.stat().st_size:
        return False
    return sha256(a) == sha256(b)


def build_latest_index(source_folders: Iterable[Path]) -> Dict[str, Tuple[str, Path]]:
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
            logging.error("backup root not found or not a directory: %s", backup_root)
            return 2

        dated_folders = list_dated_folders(backup_root)
        if not dated_folders:
            logging.error("no dated folders found in %s", backup_root)
            return 3

        target_folder = backup_root / target_date
        source_folders = [folder for folder in dated_folders if folder.name != target_date]

        if not source_folders:
            logging.error("no source dated folders found after excluding target date")
            return 3

        latest_by_name = build_latest_index(source_folders)
        if not latest_by_name:
            logging.error("no regular files found in source dated folders")
            return 3

        created_target = False
        if not target_folder.exists():
            created_target = True
            if not args.dry_run:
                target_folder.mkdir(parents=True, exist_ok=True)

        copied = 0
        overwritten = 0
        skipped = 0

        for filename in sorted(latest_by_name):
            source_date, source_path = latest_by_name[filename]
            destination_path = target_folder / filename

            if destination_path.exists():
                if files_identical(source_path, destination_path):
                    skipped += 1
                    logging.debug(
                        "SKIP  %s (already identical to source date %s)",
                        filename,
                        source_date,
                    )
                    continue

                overwritten += 1
                logging.debug("OVERWRITE %s <- %s", filename, source_date)
                if not args.dry_run:
                    shutil.copy2(source_path, destination_path)
                continue

            copied += 1
            logging.debug("COPY  %s <- %s", filename, source_date)
            if not args.dry_run:
                shutil.copy2(source_path, destination_path)

        scanned_text = ", ".join(folder.name for folder in source_folders)
        logging.info("Synthetic full backup summary")
        logging.info("backup root     : %s", backup_root)
        logging.info("target folder   : %s", target_folder)
        logging.info("target created  : %s", "yes" if created_target else "no")
        logging.info("source folders  : %s (%s)", len(source_folders), scanned_text)
        logging.info("unique filenames: %s", len(latest_by_name))
        logging.info("copied          : %s", copied)
        logging.info("overwritten     : %s", overwritten)
        logging.info("skipped         : %s", skipped)
        logging.info("dry run         : %s", "yes" if args.dry_run else "no")

        return 0
    except Exception:
        logging.critical("failed to create synthetic full backup")
        logging.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
