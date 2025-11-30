import os
import logging
import typing
import requests
import sys
import subprocess
import json
from argparse import ArgumentParser
from logging import handlers


WORK_DIR = os.path.dirname(__file__)
SCRIPT_FILE = os.path.basename(__file__)


class UpdateGitReposLogger:
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

    def critical(self: typing.Self, message: str) -> None:
        self._logger.critical(message)

    def error(self: typing.Self, message: str) -> None:
        self._logger.error(message)

    def warning(self: typing.Self, message: str) -> None:
        self._logger.warning(message)

    def info(self: typing.Self, message: str) -> None:
        self._logger.info(message)

    def debug(self: typing.Self, message: str) -> None:
        self._logger.debug(message)


def discover_git_repos(log: UpdateGitReposLogger,
                       visibility: str = None,
                       username: str = None) -> list[str]:
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

    try:
        log.info(f"Requesting endpoint {url} for repos.")
        response = requests.get(url, headers=headers, params=params)
        log.info(f"Status for discovery response: {response.status_code}.")

        if response.status_code == 401:
            log.warning("You may need to provide a valid GitHub token.")

        if response.status_code != 200:
            log.error(f"API failed {response.status_code}: {response.text}")
            return []

        return [repo["ssh_url"] for repo in response.json()]
    except Exception as e:
        log.error(f"Error while discovering repos: {e}.")
        return []


def update_local_clones(log: UpdateGitReposLogger,
                        repos_dir: str,
                        repo_urls: list[str]) -> None:
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
            subprocess.run(["git", "pull"], cwd=repo_path, check=True)
            subprocess.run(["git", "restore", "."], cwd=repo_path, check=True)
        except subprocess.CalledProcessError as e:
            log.error(f"Error while updating latest changes: {e}.")


def main() -> None:
    log = UpdateGitReposLogger()

    try:
        parser = ArgumentParser()
        parser.add_argument("-v", "--visibility", dest="visibility")
        parser.add_argument("-u", "--username", dest="username")
        parser.add_argument("repos_dir")
        args = parser.parse_args()
        repo_urls = discover_git_repos(log, args.visibility, args.username)

        update_local_clones(log, args.repos_dir, repo_urls)
    except Exception as e:
        log.critical(f"Error while updating git repos: {e}.")
        raise


if __name__ == "__main__":
    main()
