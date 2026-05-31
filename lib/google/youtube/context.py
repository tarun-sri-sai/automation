import json
import logging
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
from tempfile import NamedTemporaryFile
from lib.cache import sqlite_cache


class YouTubeContext:
    def __init__(self, client_id, client_secret, project_id):
        self._SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
        self._TOKEN_CACHE = Path("youtube-token.pkl")
        self._CRED_FILE_WEB_CONTENTS = {
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": (
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "redirect_uris": [
                "http://localhost:80/"
            ]
        }
        self._PAGE_SIZE = 50
        self._client_id = client_id
        self._client_secret = client_secret
        self._project_id = project_id
        self._creds = None
        self._client = None

    def __repr__(self):
        return (
            f"YouTubeContext(project_id={self._project_id})"
        )

    @property
    def creds(self):
        if self._TOKEN_CACHE.exists():
            logging.debug(f"cache hit for credentials at {self._TOKEN_CACHE}")
            with open(self._TOKEN_CACHE, "rb") as f:
                self._creds = pickle.load(f)

        if (
            self._creds is not None and self._creds.valid and
            not self._creds.expired
        ):
            logging.debug(f"valid credentials, not updating cache")
            return self._creds

        if self._creds is None or not self._creds.valid:
            logging.info("invalid or empty credentials, logging in...")
            cred_file_contents = {
                "web": {
                    **(self._CRED_FILE_WEB_CONTENTS),
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "project_id": self._project_id
                }
            }

            with NamedTemporaryFile(
                mode='w', delete=False, suffix='.json'
            ) as f:
                f.write(json.dumps(cred_file_contents))
                credential_file = f.name
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_file, self._SCOPES
            )
            self._creds = flow.run_local_server(port=80)

            Path(credential_file).unlink()

        if self._creds.expired and self._creds.refresh_token:
            logging.info("credentials expired, refreshing...")
            self._creds.refresh(Request())

        logging.debug(f"caching token at {self._TOKEN_CACHE}")
        with open(self._TOKEN_CACHE, "wb") as f:
            pickle.dump(self._creds, f)

        logging.info("initialized google credentials")
        return self._creds
    
    @property
    def client(self):
        if self._client is not None:
            return self._client
        
        self._client = build('youtube', 'v3', credentials=self.creds)
        logging.info("initialized youtube client")
        return self._client

    @sqlite_cache()
    def get_subscriptions(self):
        subscriptions = []
        next_page_token = None

        logging.info("fetching all subscriptions...")
        while True:
            request = self.client.subscriptions().list(
                part='snippet,contentDetails', mine=True,
                maxResults=self._PAGE_SIZE, pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                subscriptions.append({
                    'channel_id': item['snippet']['resourceId']['channelId'],
                    'channel_title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': (
                        item['snippet']['thumbnails']['default']['url']
                    )
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

            logging.debug(f"next page for subscriptions: {next_page_token}")

        return subscriptions


    @sqlite_cache()
    def get_channel_stats(self, channel_ids):
        stats = {}

        logging.info(f"fetching stats for {len(channel_ids)} channels...")
        for i in range(0, len(channel_ids), self._PAGE_SIZE):
            logging.debug(f"fetching batch [{i + 1}, {i + self._PAGE_SIZE}]")
            batch = channel_ids[i:i+self._PAGE_SIZE]
            request = self.client.channels().list(
                part='statistics,contentDetails', id=','.join(batch)
            )
            response = request.execute()

            for item in response.get('items', []):
                channel_id = item['id']
                logging.debug(
                    f"stats for channel {channel_id}: {item['statistics']}"
                )
                stats[channel_id] = {
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'subscriber_count': (
                        item['statistics'].get('subscriberCount', 'Hidden')
                    ),
                    'video_count': int(item['statistics'].get('videoCount', 0))
                }

        return stats
