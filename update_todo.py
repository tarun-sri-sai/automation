import os
import git
import logging
import datetime
import traceback
from argparse import ArgumentParser
from lib.logging_util import setup_logger


def commit_daily_copy(repo: git.Repo):
    today = datetime.date.today()
    date_fmt = "%Y-%m-%d"
    yesterday = (today - datetime.timedelta(days=1)).strftime(date_fmt)

    if repo.head.commit.message.strip() == yesterday:
        logging.info("yesterday's to-do file already exists")
        return

    logging.info("committing to-do.txt copy to the repo")
    repo.index.add(["to-do.txt"])

    if not repo.index.diff("HEAD"):
        logging.info("no change since last commit")
        return

    repo.index.commit(yesterday)
    logging.info(f'commit made with message "{yesterday}" successfully')


def push_to_origin(repo: git.Repo):
    try:
        branch = repo.active_branch.name
        logging.info(f'pushing branch "{branch}" to origin')

        repo.remote(name="origin").push(
            refspec=f"{branch}:{branch}",
            set_upstream=True
        )

        logging.info("push completed successfully")
    except Exception as e:
        logging.warning(f"push failed: {e}")


def main():
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
        logging.critical("failed to update to-do")
        logging.critical(traceback.print_exc())


if __name__ == '__main__':
    main()
