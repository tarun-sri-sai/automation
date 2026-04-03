import json
import logging
import os
import re
import requests
import subprocess
import sys
import time
from argparse import ArgumentParser
from logging import handlers


WORK_DIR = os.path.dirname(__file__)
SCRIPT_FILE = os.path.basename(__file__)


def setup_logger(
    name,
    log_file,
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


def get_repo_url(repo, ssh_host=None, use_ssh=None):
    if ssh_host:
        return re.sub(r"git@[^:]+:", f"{ssh_host}:", repo["ssh_url"])

    return repo["ssh_url"] if use_ssh else repo["clone_url"]


def discover_git_repos(visibility=None, username=None, ssh_host=None, use_ssh=None):
    url = "https://api.github.com/user/repos"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        bearer_token = os.environ.get("GITHUB_TOKEN")
        if bearer_token:
            log.info("Using bearer token from environment.")
            headers["Authorization"] = f"Bearer {bearer_token}"
        else:
            log.warning("No bearer token found in environment.")
    except Exception as e:
        log.warning(f"Environment variable not given, it's ok: {e}.")

    params = {}
    if bearer_token:
        params["affiliation"] = "owner"
        if visibility in ["public", "private"]:
            params["visibility"] = visibility
    else:
        if not username:
            log.error(f"Pass --username <github-username> for public repos")
            return []

        url = f"https://api.github.com/users/{username}/repos"
        params["visibility"] = "public"
        log.info("Unauthenticated requests can only access public repositories.")

    log.info(f"Params: {json.dumps(params, indent=2)}")

    repo_urls = []
    try:
        while url:
            log.info(f"Requesting endpoint {url} for repos.")
            response = requests.get(url, headers=headers, params=params)
            log.info(f"Status for discovery response: {response.status_code}.")

            if response.status_code == 401:
                log.warning("You may need to provide a valid GitHub token.")

            if response.status_code != 200:
                log.error(f"API {response.status_code}: {response.text}")
                return []

            curr_repos = [
                get_repo_url(repo, ssh_host, use_ssh)
                for repo in response.json()
            ]
            log.info(f"Discovered {len(curr_repos)} repos in current page.")
            repo_urls += curr_repos

            url = response.links.get("next", {}).get("url")
            if url:
                sleep_secs = 10
                log.info(f"Sleeping for {sleep_secs}s before requesting {url}.")
                time.sleep(sleep_secs)

        return repo_urls
    except Exception as e:
        log.error(f"Error while discovering repos: {e}.")
        return []


def update_local_clones(repos_dir, repo_urls):
    for url in repo_urls:
        repo_name = os.path.basename(url).replace(".git", "")
        repo_path = os.path.join(repos_dir, repo_name)

        if os.path.exists(repo_path):
            log.info(f"Repository {repo_name} already exists. "
                     f"Pulling latest changes.")
        else:
            log.info(f"Cloning repository {repo_name}.")
            subprocess.run(["git", "clone", url, repo_path], check=True)
        try:
            subprocess.run(["git", "fetch", "--all"], cwd=repo_path, check=True)
        except subprocess.CalledProcessError as e:
            log.error(f"Error while updating latest changes: {e}.")


def main():
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
            help="Directory to clone/update repositories into"
        )
        args = parser.parse_args()

        repo_urls = discover_git_repos(
            args.visibility,
            args.username,
            args.ssh_host,
            args.use_ssh
        )

        if args.dry_run:
            log.info("Dry run mode - discovered repo URLs:")
            log.info(json.dumps(repo_urls, indent=2))
        else:
            update_local_clones(args.repos_dir, repo_urls)
    except Exception as e:
        log.critical(f"Error while updating git repos: {e}.")
        raise


if __name__ == "__main__":
    main()
