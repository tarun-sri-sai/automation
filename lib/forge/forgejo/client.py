import os
import requests
import warnings
from lib.forge.client import Client

warnings.filterwarnings("ignore")


FORGEJO_HOST = os.getenv("FORGEJO_HOST")
FORGEJO_TOKEN = os.getenv("FORGEJO_TOKEN")


class ForgejoClient(Client):
    def __init__(self, verify_ssl=False):
        self._headers = {
            "Accept": "application/json",
        }

        self._verify_ssl = verify_ssl

        if FORGEJO_TOKEN:
            self._headers["Authorization"] = f"Bearer {FORGEJO_TOKEN}"

    def is_authenticated(self):
        return "Authorization" in self._headers

    def build_url(self, endpoint):
        return f"{FORGEJO_HOST}{endpoint}"

    def make_request(self, method, endpoint=None, full_url=None, **kwargs):
        kwargs["headers"] = {
            **self._headers,
            **kwargs.get("headers", {})
        }
        kwargs["verify"] = self._verify_ssl
        url = full_url or self.build_url(endpoint)

        response = requests.request(method, url, **kwargs)
        response.raise_for_status()

        return response
