import os
import requests
from lib.forge.client import Client

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class GithubClient(Client):
    def __init__(self):
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if GITHUB_TOKEN:
            self._headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    def is_authenticated(self):
        return "Authorization" in self._headers

    def make_request(self, method, endpoint, **kwargs):
        kwargs["headers"] = {
            **self._headers,
            **kwargs.get("headers", {})
        }
        url = f"https://api.github.com{endpoint}"

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()

        return response
