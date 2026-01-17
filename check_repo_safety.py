from argparse import ArgumentParser
from git import Repo, InvalidGitRepositoryError
from pathlib import Path


def check_repo_safety(repo: Repo, repo_name: str):
    is_dirty = repo.is_dirty()

    log_output = repo.git.log('--branches', '--not', '--remotes', '--oneline')
    unpushed_commits = len(log_output.splitlines())

    if not (is_dirty or unpushed_commits):
        return

    print(f"{repo_name}:")

    if is_dirty:
        print(f"  - has uncommitted changes")

    if unpushed_commits:
        print(f"  - [{unpushed_commits}] unpushed commits")


def validate_repos(directory: Path):
    for item in directory.iterdir():
        if not item.is_dir():
            continue

        try:
            repo = Repo(item)
        except InvalidGitRepositoryError:
            print(f"the directory [{item}] is not a Git repo")
            continue

        check_repo_safety(repo, item.name)


def main():
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
