import os
import git
import sys
import typing
import logging
import datetime
import traceback
from logging import handlers
from argparse import ArgumentParser


WORK_DIR = os.path.dirname(__file__)
SCRIPT_FILE = os.path.basename(__file__)


class UpdateTodoLogger:
    def __init__(self: typing.Self):
        self._logger = logging.getLogger()

        log_file_name = os.path.splitext(SCRIPT_FILE)[0] + ".log"
        log_file_dir = os.path.join(WORK_DIR, "logs")
        os.makedirs(log_file_dir, exist_ok=True)
        log_file = os.path.join(log_file_dir, log_file_name)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s")

        log_file_size = 5 * int(1024 ** 2)
        rf_handler = handlers.RotatingFileHandler(
            log_file, maxBytes=log_file_size, backupCount=2)
        rf_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        self._logger.addHandler(rf_handler)
        self._logger.addHandler(console_handler)
        self._logger.setLevel(logging.INFO)

    def info(self: typing.Self, message: str) -> None:
        self._logger.info(message)

    def critical(self: typing.Self, message: str) -> None:
        self._logger.critical(message)


log = UpdateTodoLogger()


def main():
    try:
        parser = ArgumentParser(description="create a daily copy of to-do file")
        parser.add_argument(
            "directory",
            type=str,
            help="path to the directory containing to-do copies"
        )
        args = parser.parse_args()

        repo = git.Repo(args.directory)

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
    except Exception as e:
        log.critical("failed to update to-do")
        log.critical(traceback.print_exc())


if __name__ == '__main__':
    main()
