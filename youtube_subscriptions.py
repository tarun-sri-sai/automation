import json
import logging
import pickle
from argparse import ArgumentParser
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path
from tempfile import NamedTemporaryFile
from lib.encryption import read_password
from lib.logging_util import setup_logger

PAGE_SIZE = 50


class GoogleOAuth2Credential:
    def __init__(self, client_id, client_secret, project_id):
        self._SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
        self._TOKEN_CACHE = Path("youtube-subscriptions-token.pkl")
        self._CRED_FILE_WEB_CONTENTS = {
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [
                "http://localhost:80/"
            ]
        }
        self._client_id = client_id
        self._client_secret = client_secret
        self._project_id = project_id
        self._creds = None

    @property
    def creds(self):
        if self._TOKEN_CACHE.exists():
            logging.debug(f"cache hit for credentials at {self._TOKEN_CACHE}")
            with open(self._TOKEN_CACHE, "rb") as f:
                self._creds = pickle.load(f)

        if (
            self._creds is not None and
            self._creds.valid and
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
                mode='w',
                delete=False,
                suffix='.json'
            ) as f:
                f.write(json.dumps(cred_file_contents))
                credential_file = f.name
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_file, self._SCOPES
            )
            self._creds = flow.run_local_server(port=80)

        if self._creds.expired and self._creds.refresh_token:
            logging.info("credentials expired, refreshing...")
            self._creds.refresh(Request())

        logging.debug(f"caching token at {self._TOKEN_CACHE}")
        with open(self._TOKEN_CACHE, "wb") as f:
            pickle.dump(self._creds, f)

        return self._creds


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")


def get_subscriptions(youtube):
    subscriptions = []
    next_page_token = None

    logging.info("fetching all subscriptions...")
    while True:
        request = youtube.subscriptions().list(
            part='snippet,contentDetails',
            mine=True,
            maxResults=PAGE_SIZE,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get('items', []):
            subscriptions.append({
                'channel_id': item['snippet']['resourceId']['channelId'],
                'channel_title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'thumbnail': item['snippet']['thumbnails']['default']['url']
            })

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

        logging.debug(f"next page for subscriptions: {next_page_token}")

    return subscriptions


def get_channel_stats(youtube, channel_ids):
    stats = {}

    logging.debug(f"fetching stats for channels...")
    for i in range(0, len(channel_ids), PAGE_SIZE):
        logging.debug(f"fetching batch [{i + 1}, {i + PAGE_SIZE}]")
        batch = channel_ids[i:i+PAGE_SIZE]
        request = youtube.channels().list(
            part='statistics,contentDetails',
            id=','.join(batch)
        )
        response = request.execute()

        for item in response.get('items', []):
            channel_id = item['id']
            stats[channel_id] = {
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'subscriber_count': item['statistics'].get('subscriberCount', 'Hidden'),
                'video_count': int(item['statistics'].get('videoCount', 0))
            }

    return stats


def main():
    init_logger()

    parser = ArgumentParser(
        description="create report on youtube subscriptions"
    )
    parser.add_argument(
        "client_id",
        type=str,
        help="oauth2 client ID"
    )
    parser.add_argument(
        "project_id",
        type=str,
        help="project ID"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output.json",
        help="output file name (default: output.json)"
    )
    args = parser.parse_args()

    google_cred = GoogleOAuth2Credential(
        args.client_id,
        read_password("client secret: "),
        args.project_id
    )
    logging.info("initialized google credentials")

    youtube = build('youtube', 'v3', credentials=google_cred.creds)
    subscriptions = get_subscriptions(youtube)
    stats = get_channel_stats(
        youtube,
        tuple(s["channel_id"] for s in subscriptions)
    )

    output_path = Path(args.output)
    logging.debug(f"writing to {output_path}...")
    with open(output_path, "w") as f:
        json.dump([
            {
                "channel_id": s["channel_id"],
                "channel_title": s["channel_title"],
                "description": s["description"],
                "view_count": stats[s["channel_id"]]["view_count"],
                "subscriber_count": stats[s["channel_id"]]["subscriber_count"],
                "video_count": stats[s["channel_id"]]["video_count"]
            }
            for s in subscriptions
        ], f, indent=2)
    
    logging.info(f"done! output written to {output_path}")


if __name__ == "__main__":
    main()
