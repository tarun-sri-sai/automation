import logging
from argparse import ArgumentParser
from git import Repo, InvalidGitRepositoryError
from pathlib import Path
from lib.logging_util import setup_logger


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


def check_repo_safety(repo: Repo, repo_name: str):
    logging.debug(f"checking repo safety for {repo_name}")
    repo_status = {}

    repo_status["is_dirty"] = repo.is_dirty()

    log_output = repo.git.log('--branches', '--not', '--remotes', '--oneline')
    repo_status["unpushed_commits"] = len(log_output.splitlines())

    if not any(repo_status.values()):
        return

    repo_status_message = " ".join(
        (
            f"{k}"
            if isinstance(v, bool)
            else f"{k}={v}"
        )
        for k, v in repo_status.items()
        if v
    )
    logging.info(f"{repo_name}: {repo_status_message}")


def validate_repos(directory: Path):
    for item in directory.iterdir():
        if not item.is_dir():
            continue

        try:
            repo = Repo(item)
        except InvalidGitRepositoryError:
            logging.error(f"the directory [{item}] is not a git repo")
            continue

        check_repo_safety(repo, item.name)


def main():
    init_logger()

    parser = ArgumentParser(
        "check_repo_safety",
        description="checks whether the local Git repos are safe to delete"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="path to a directory containing all the local Git repos"
    )

    args = parser.parse_args()

    validate_repos(Path(args.directory))


if __name__ == '__main__':
    main()
