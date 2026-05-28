import asyncio
import logging
import os
import re
import requests
import shutil
from argparse import ArgumentParser
from git import Repo
from git.exc import NoSuchPathError, InvalidGitRepositoryError
from pathlib import Path
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


async def discover_git_repos(
    visibility=None,
    username=None,
    ssh_host=None,
    use_ssh=None
):
    url = "https://api.github.com/user/repos"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        bearer_token = os.environ.get("GITHUB_TOKEN")
        if bearer_token:
            logging.info("Using bearer token from environment.")
            headers["Authorization"] = f"Bearer {bearer_token}"
        else:
            logging.warning("No bearer token found in environment.")
    except Exception as e:
        logging.warning(f"Environment variable not given, it's ok: {e}.")

    params = {}

    if username:
        url = f"https://api.github.com/users/{username}/repos"
    elif bearer_token:
        params["affiliation"] = "owner"
    else:
        logging.error(f"Pass --username <github-username> for public repos")
        return []

    if bearer_token:
        if visibility in ["public", "private"]:
            params["visibility"] = visibility
    else:
        logging.info(
            "Unauthenticated requests can only access public repos."
        )
        params["visibility"] = "public"

    logging.info(f"Params: {params}")

    repo_urls = {}
    try:
        while url:
            logging.info(f"Requesting endpoint {url} for repos.")
            response = requests.get(url, headers=headers, params=params)
            logging.info(
                f"Status for discovery response: {response.status_code}."
            )

            if response.status_code == requests.codes.unauthorized:
                logging.warning(
                    "You may need to provide a valid GitHub token."
                )

            if response.status_code != requests.codes.ok:
                logging.error(f"API {response.status_code}: {response.text}")
                return {}

            curr_repos = {
                repo["name"]: await get_repo_url(repo, ssh_host, use_ssh)
                for repo in response.json()
            }
            logging.info(
                f"Discovered {len(curr_repos)} repos in current page."
            )
            repo_urls = {**repo_urls, **curr_repos}

            url = response.links.get("next", {}).get("url")
            if url:
                sleep_secs = 10
                logging.info(
                    f"Sleeping for {sleep_secs}s before requesting {url}."
                )
                await asyncio.sleep(sleep_secs)

        return repo_urls
    except Exception as e:
        logging.error(f"Error while discovering repos: {e}.")
        return {}


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
    for name, url in repo_urls.items():
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
            "-s",
            "--ssh-host",
            help="Custom SSH host (uses SSH instead of HTTPS for cloning repo)"
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

        repo_urls = await discover_git_repos(
            args.visibility,
            args.username,
            args.ssh_host,
            args.use_ssh
        )

        if args.dry_run:
            logging.info("Dry run mode - discovered repo URLs:")
            logging.info(repo_urls)
        else:
            await update_local_clones(args.repos_dir, repo_urls)
    except Exception as e:
        logging.critical(f"Error while updating git repos: {e}.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
