from lib.forge.repos import Repos


class GithubRepos(Repos):
    def __init__(self, client, visibility=None, username=None, props=None):
        self._client = client
        self._username = username
        self._visibility = visibility

        self._props = props
        if self._props is None:
            self._props = ["full_name"]

    def get(self):
        url = "/user/repos"
        params = {}

        if self._username:
            url = f"/users/{self._username}/repos"
        elif self._client.is_authenticated():
            params["affiliation"] = "owner"
        else:
            raise ValueError("missing username for public repos")

        if self._client.is_authenticated():
            if self._visibility in ["public", "private"]:
                params["visibility"] = self._visibility
        else:
            params["visibility"] = "public"

        headers = {
            "X-GitHub-Api-Version": "2022-11-28"
        }

        result = []
        while url:
            response = self._client.make_request(
                "GET", url, params=params, headers=headers
            )
            result += [
                {k: i.get(k) for k in self._props}
                for i in response.json()
            ]

            url = response.links.get("next", {}).get("url")

        return result
