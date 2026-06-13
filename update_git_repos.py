import asyncio
import logging
import os
import re
import shutil
from argparse import ArgumentParser
from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError
from pathlib import Path
from lib.forge.github.client import GithubClient
from lib.forge.github.repos import GithubRepos
from lib.logging_util import setup_logger

semaphore = asyncio.Semaphore(10)

logging.getLogger("git").setLevel(logging.WARNING)
logging.getLogger("git.cmd").setLevel(logging.WARNING)


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


async def get_repo_url(repo, ssh_host=None, use_ssh=None):
    if ssh_host:
        return re.sub(r"git@[^:]+:", f"{ssh_host}:", repo["ssh_url"])

    return repo["ssh_url"] if use_ssh else repo["clone_url"]


def _update_local_clone(repo_name, repo_path, repo_url):
    repo_obj = None
    try:
        repo_obj = Repo(repo_path)
    except NoSuchPathError:
        logging.info(f"{repo_name}: Cloning repo.")
        repo_obj = Repo.clone_from(repo_url, repo_path)
    except InvalidGitRepositoryError:
        logging.warning(
            f"{repo_name}: Directory {repo_path} exists but is not a repo. "
            f"Re-cloning."
        )
        shutil.rmtree(repo_path)
        repo_obj = Repo.clone_from(repo_url, repo_path)

    logging.info(f"{repo_name}: Fetching latest changes.")
    for remote in repo_obj.remotes:
        try:
            logging.info(f"{repo_name}: Updating remote {remote}.")
            remote.fetch()
        except Exception as e:
            logging.error(f"{repo_name}: Error updating {remote}: {e}.")

    logging.info(f"{repo_name}: Successfully updated.")


async def update_local_clone(repo_name, repo_path, repo_url):
    async with semaphore:
        await asyncio.to_thread(
            _update_local_clone,
            repo_name,
            repo_path,
            repo_url
        )


async def update_local_clones(repos_dir, repo_urls):
    tasks = []
    for name, url in repo_urls:
        repo_path = os.path.join(repos_dir, name)

        tasks.append(update_local_clone(name, repo_path, url))

    await asyncio.gather(*tasks)


async def main():
    init_logger()

    try:
        parser = ArgumentParser()
        parser.add_argument(
            "-v",
            "--visibility",
            help="Repo visibility ('public', 'private')"
        )
        parser.add_argument(
            "-u",
            "--username",
            help="GitHub username"
        )
        parser.add_argument(
            "-l",
            "--use-ssh",
            action="store_true",
            help="Uses SSH instead of HTTPS for cloning repo"
        )
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            help="Print discovered repo URLs without cloning/updating"
        )
        parser.add_argument(
            "repos_dir",
            help="Directory to clone/update repos into"
        )
        args = parser.parse_args()

        props = ["name", "clone_url"]
        if args.use_ssh:
            props = ["name", "ssh_url"]

        client = GithubClient()
        gh_repos = GithubRepos(client, args.visibility, args.username, props)
        repo_urls = [[i[props[0]], i[props[1]]] for i in gh_repos.get()]

        if args.dry_run:
            logging.info("Dry run mode - discovered repo URLs:")
            logging.info(repo_urls)
        else:
            await update_local_clones(args.repos_dir, repo_urls)
    except Exception as e:
        logging.critical(f"error while updating git repos: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
