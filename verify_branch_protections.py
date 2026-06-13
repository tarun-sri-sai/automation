import logging
from argparse import ArgumentParser
from pathlib import Path
from lib.forge.gitea.branch_protections import GiteaBranchProtections
from lib.forge.gitea.client import GiteaClient
from lib.forge.gitea.repos import GiteaRepos
from lib.forge.github.branch_protections import GithubBranchProtections
from lib.forge.github.client import GithubClient
from lib.forge.github.repos import GithubRepos
from lib.logging_util import setup_logger


class BranchProtectionVerifier:
    def __init__(self):
        gitea_client = GiteaClient()
        gitea_repos = GiteaRepos(gitea_client)

        gh_client = GithubClient()
        gh_repos = GithubRepos(gh_client, visibility="public")

        self._forges = {
            "gitea": GiteaBranchProtections(gitea_client, gitea_repos),
            "github": GithubBranchProtections(gh_client, gh_repos)
        }

    def get_forges(self):
        return list(self._forges.keys())
    
    def verify(self, forge):
        self._forges[forge].verify()


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


def main():
    init_logger()

    verifier = BranchProtectionVerifier()

    parser = ArgumentParser(
        description="checks the branch protections for all repos in a forge"
    )
    parser.add_argument(
        "forge", 
        type=str,
        help=(
            f"name of the forge (values: {verifier.get_forges()})"
        )
    )
    args = parser.parse_args()

    try:
        verifier.verify(args.forge)
    except Exception as e:
        logging.critical(f"error verifying branch protections: {e}", exc_info=True)


if __name__ == '__main__':
    main()
