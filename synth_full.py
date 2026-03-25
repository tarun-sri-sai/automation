import argparse
import datetime as dt
import hashlib
import logging
import os
import shutil
import sys
import traceback
from logging import handlers
from pathlib import Path
from typing import Dict, Iterable, Tuple


WORK_DIR = os.path.dirname(__file__)
SCRIPT_FILE = os.path.basename(__file__)


def setup_logger(
    name: str,
    log_file: str,
    level=logging.INFO,
    max_bytes=5 * 1024 * 1024,
    backup_count=2,
):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # avoid duplicate logs

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler = handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


log = setup_logger(
    __name__,
    os.path.join(WORK_DIR, "logs", os.path.splitext(SCRIPT_FILE)[0] + ".log"),
)


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
    try:
        args = parse_args()

        backup_root = Path(args.backup_root).expanduser().resolve()
        target_date = dt.date.today().strftime("%Y%m%d")

        if not backup_root.exists() or not backup_root.is_dir():
            log.error("backup root not found or not a directory: %s", backup_root)
            return 2

        dated_folders = list_dated_folders(backup_root)
        if not dated_folders:
            log.error("no dated folders found in %s", backup_root)
            return 3

        target_folder = backup_root / target_date
        source_folders = [folder for folder in dated_folders if folder.name != target_date]

        if not source_folders:
            log.error("no source dated folders found after excluding target date")
            return 3

        latest_by_name = build_latest_index(source_folders)
        if not latest_by_name:
            log.error("no regular files found in source dated folders")
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
                    log.debug(
                        "SKIP  %s (already identical to source date %s)",
                        filename,
                        source_date,
                    )
                    continue

                overwritten += 1
                log.debug("OVERWRITE %s <- %s", filename, source_date)
                if not args.dry_run:
                    shutil.copy2(source_path, destination_path)
                continue

            copied += 1
            log.debug("COPY  %s <- %s", filename, source_date)
            if not args.dry_run:
                shutil.copy2(source_path, destination_path)

        scanned_text = ", ".join(folder.name for folder in source_folders)
        log.info("Synthetic full backup summary")
        log.info("backup root     : %s", backup_root)
        log.info("target folder   : %s", target_folder)
        log.info("target created  : %s", "yes" if created_target else "no")
        log.info("source folders  : %s (%s)", len(source_folders), scanned_text)
        log.info("unique filenames: %s", len(latest_by_name))
        log.info("copied          : %s", copied)
        log.info("overwritten     : %s", overwritten)
        log.info("skipped         : %s", skipped)
        log.info("dry run         : %s", "yes" if args.dry_run else "no")

        return 0
    except Exception:
        log.critical("failed to create synthetic full backup")
        log.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
