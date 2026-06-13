from lib.forge.repos import Repos


class GiteaRepos(Repos):
    def __init__(self, client, props=None):
        self._client = client

        self._props = props
        if self._props is None:
            self._props = ["full_name"]

    def get(self):
        response = self._client.make_request("GET", "/api/v1/user/repos")

        return [
            {k: i.get(k) for k in self._props}
            for i in response.json()
        ]
