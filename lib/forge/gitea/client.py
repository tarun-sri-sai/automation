import os
import requests
import warnings
from lib.forge.client import Client

warnings.filterwarnings("ignore")


GITEA_HOST = os.getenv("GITEA_HOST")
GITEA_TOKEN = os.getenv("GITEA_TOKEN")


class GiteaClient(Client):
    @staticmethod
    def get_host():
        return GITEA_HOST

    @staticmethod
    def make_request(*args, **kwargs):
        headers = {
            "Authorization": f"Bearer {GITEA_TOKEN}",
            "Accept": "application/json"
        }
        kwargs["headers"] = {
            **headers,
            **kwargs.get("headers", {})
        }

        kwargs["verify"] = False

        response = requests.request(*args, **kwargs)
        response.raise_for_status()
        return response.json()
