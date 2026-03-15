import os
import git
import sys
import logging
import datetime
import traceback
from logging import handlers
from argparse import ArgumentParser


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
        backupCount=backup_count
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


def commit_daily_copy(repo: git.Repo):
    today = datetime.date.today()
    date_fmt = "%Y-%m-%d"
    yesterday = (today - datetime.timedelta(days=1)).strftime(date_fmt)

    if repo.head.commit.message.strip() == yesterday:
        log.info("yesterday's to-do file already exists")
        return

    log.info("committing to-do.txt copy to the repo")
    repo.index.add(["to-do.txt"])

    if not repo.index.diff("HEAD"):
        log.info("no change since last commit")
        return

    repo.index.commit(yesterday)
    log.info(f'commit made with message "{yesterday}" successfully')


def push_to_origin(repo: git.Repo):
    try:
        branch = repo.active_branch.name
        log.info(f'pushing branch "{branch}" to origin')

        repo.remote(name="origin").push(
            refspec=f"{branch}:{branch}",
            set_upstream=True
        )

        log.info("push completed successfully")
    except Exception as e:
        log.warning(f"push failed: {e}")


def main():
    parser = ArgumentParser(description="create a daily copy of to-do file")
    parser.add_argument(
        "directory",
        type=str,
        help="path to the directory containing to-do copies"
    )
    args = parser.parse_args()

    try:
        repo = git.Repo(args.directory)
        commit_daily_copy(repo)
        push_to_origin(repo)
    except Exception as _:
        log.critical("failed to update to-do")
        log.critical(traceback.print_exc())


if __name__ == '__main__':
    main()
