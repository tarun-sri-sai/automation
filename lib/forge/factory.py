from lib.forge.gitea.client import GiteaClient
from lib.forge.gitea.repos import GiteaRepos
from lib.forge.gitea.branch_protections import GiteaBranchProtections
from lib.forge.github.client import GithubClient
from lib.forge.github.repos import GithubRepos
from lib.forge.github.branch_protections import GithubBranchProtections
from lib.forge.forgejo.client import ForgejoClient
from lib.forge.forgejo.repos import ForgejoRepos
from lib.forge.forgejo.branch_protections import ForgejoBranchProtections


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
        elif self._forge == "forgejo":
            forgejo_client = ForgejoClient()
            forgejo_repos = ForgejoRepos(forgejo_client)
            return ForgejoBranchProtections(forgejo_client, forgejo_repos)
        else:
            raise ValueError(f"unsupported forge: {self._forge}")
