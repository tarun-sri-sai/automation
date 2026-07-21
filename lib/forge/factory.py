from lib.forge.gitea.client import GiteaClient
from lib.forge.gitea.repos import GiteaRepos
from lib.forge.gitea.branch_protections import GiteaBranchProtections
from lib.forge.github.client import GithubClient
from lib.forge.github.repos import GithubRepos
from lib.forge.github.branch_protections import GithubBranchProtections


class Factory:
    def __init__(self, forge):
        self._forge = forge

    def build_branch_protections(self):
        if self._forge == "gitea":
            gitea_client = GiteaClient()
            gitea_repos = GiteaRepos(gitea_client)
            return GiteaBranchProtections(gitea_client, gitea_repos)
        elif self._forge == "github":
            gh_client = GithubClient()
            gh_repos = GithubRepos(gh_client, visibility="public")
            return GithubBranchProtections(gh_client, gh_repos)
        else:
            raise ValueError(f"unsupported forge: {self._forge}")
