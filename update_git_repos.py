import json
import logging
import os
import re
import requests
import subprocess
import time
from argparse import ArgumentParser
from lib.logging_util import setup_logger


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
        logging.info("Unauthenticated requests can only access public repositories.")
        params["visibility"] = "public"

    logging.info(f"Params: {json.dumps(params, indent=2)}")

    repo_urls = []
    try:
        while url:
            logging.info(f"Requesting endpoint {url} for repos.")
            response = requests.get(url, headers=headers, params=params)
            logging.info(f"Status for discovery response: {response.status_code}.")

            if response.status_code == requests.codes.unauthorized:
                logging.warning("You may need to provide a valid GitHub token.")

            if response.status_code != requests.codes.ok:
                logging.error(f"API {response.status_code}: {response.text}")
                return []

            curr_repos = [
                get_repo_url(repo, ssh_host, use_ssh)
                for repo in response.json()
            ]
            logging.info(f"Discovered {len(curr_repos)} repos in current page.")
            repo_urls += curr_repos

            url = response.links.get("next", {}).get("url")
            if url:
                sleep_secs = 10
                logging.info(f"Sleeping for {sleep_secs}s before requesting {url}.")
                time.sleep(sleep_secs)

        return repo_urls
    except Exception as e:
        logging.error(f"Error while discovering repos: {e}.")
        return []


def update_local_clones(repos_dir, repo_urls):
    for url in repo_urls:
        repo_name = os.path.basename(url).replace(".git", "")
        repo_path = os.path.join(repos_dir, repo_name)

        if os.path.exists(repo_path):
            logging.info(f"Repository {repo_name} already exists. "
                     f"Pulling latest changes.")
        else:
            logging.info(f"Cloning repository {repo_name}.")
            subprocess.run(["git", "clone", url, repo_path], check=True)
        try:
            subprocess.run(["git", "fetch", "--all"], cwd=repo_path, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while updating latest changes: {e}.")


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
            logging.info("Dry run mode - discovered repo URLs:")
            logging.info(json.dumps(repo_urls, indent=2))
        else:
            update_local_clones(args.repos_dir, repo_urls)
    except Exception as e:
        logging.critical(f"Error while updating git repos: {e}.")
        raise


if __name__ == "__main__":
    main()
