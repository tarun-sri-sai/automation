from lib.forge.repos import Repos
from .client import GiteaClient


class GiteaRepos(Repos):
    def get():
        url = f"{GiteaClient.get_host()}/api/v1/user/repos"
        response = GiteaClient.make_request("GET", url)
        return [i.get("full_name") for i in response]
