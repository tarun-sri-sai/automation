import json
import logging
import pickle
import re
import threading
from bisect import bisect_left
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path
from tempfile import NamedTemporaryFile
from lib.cache import sqlite_cache


logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


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
        self._creds_lock = threading.Lock()

    def __repr__(self):
        return (
            f"YouTubeContext(project_id={self._project_id})"
        )

    @property
    def creds(self):
        with self._creds_lock:
            if self._creds is None and self._TOKEN_CACHE.exists():
                logging.debug(
                    f"cache hit for credentials at {self._TOKEN_CACHE}"
                )
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

    def _get_client(self):
        return build('youtube', 'v3', credentials=self.creds)

    @sqlite_cache()
    def _get_subscriptions(self):
        subscriptions = []
        next_page_token = None

        logging.info("fetching all subscriptions...")
        while True:
            request = self._get_client().subscriptions().list(
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
    def _get_channel_stats(self, channel_ids):
        stats = {}

        logging.info(f"fetching stats for {len(channel_ids)} channels...")
        for i in range(0, len(channel_ids), self._PAGE_SIZE):
            logging.debug(f"fetching batch [{i + 1}, {i + self._PAGE_SIZE}]")
            batch = channel_ids[i:i+self._PAGE_SIZE]
            request = self._get_client().channels().list(
                part='statistics,contentDetails', id=','.join(batch)
            )
            response = request.execute()

            for item in response.get('items', []):
                channel_id = item['id']
                logging.debug(
                    f"stats for channel {channel_id}: {item['statistics']}"
                )
                stats[channel_id] = {
                    'view_count': int(item['statistics'].get('viewCount', -1)),
                    'subscriber_count': int(
                        item['statistics'].get('subscriberCount', -1)
                    ),
                    'video_count': int(item['statistics'].get('videoCount', -1))
                }

        return stats

    @sqlite_cache()
    def _get_upload_playlists(self, channel_ids):
        logging.info(
            f"fetching upload playlists for {len(channel_ids)} channels..."
        )

        result = {}
        for i in range(0, len(channel_ids), self._PAGE_SIZE):
            batch = list(channel_ids[i:i+self._PAGE_SIZE])
            response = self._get_client().channels().list(
                part="contentDetails",
                id=",".join(batch)
            ).execute()
            for item in response.get("items", []):
                result[item["id"]] = (
                    item["contentDetails"]["relatedPlaylists"]["uploads"]
                )

        return result

    @sqlite_cache()
    def _get_recent_videos(self, playlist_id, since):
        logging.info(f"fetching recent videos for playlist {playlist_id}...")

        try:
            since = datetime.fromisoformat(since)
            videos = {playlist_id: []}
            next_page_token = None

            while True:
                response = self._get_client().playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=self._PAGE_SIZE,
                    pageToken=next_page_token
                ).execute()

                done = False

                items = sorted((
                    datetime.fromisoformat(
                        i["contentDetails"]["videoPublishedAt"]
                    ) for i in response.get("items", [])
                ), reverse=True)

                cutoff = bisect_left(
                    [-t.timestamp() for t in items], -since.timestamp()
                )
                videos[playlist_id].extend(
                    {"published_at": item} for item in items[:cutoff]
                )
                if cutoff < len(items):
                    done = True

                next_page_token = response.get("nextPageToken")
                if done or not next_page_token:
                    break

                logging.debug(
                    f"next page for playlist {playlist_id}: {next_page_token}"
                )

            videos[playlist_id].sort(
                key=lambda x: -x["published_at"].timestamp()
            )
            return videos

        except HttpError:
            logging.warning(
                f"error fetching videos for playlist {playlist_id}, skipping..."
            )
            return {playlist_id: []}

    def _get_recent_video_stats(self, channel_ids, since):
        logging.info(
            f"fetching recent video stats for {len(channel_ids)} channels..."
        )

        recent_videos = {}

        upload_playlists = self._get_upload_playlists(channel_ids)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for channel_id in channel_ids:
                playlist_id = upload_playlists[channel_id]
                if playlist_id:
                    futures.append(executor.submit(
                        self._get_recent_videos, playlist_id, since
                    ))

            for future in as_completed(futures):
                recent_videos.update(future.result())

        return {
            channel_id: (
                {
                    "videos_last_year": (
                        len(recent_videos[upload_playlists[channel_id]])
                    ),
                    "last_video_date": datetime.isoformat(recent_videos[
                        upload_playlists[channel_id]
                    ][0]["published_at"])
                }
                if recent_videos[upload_playlists[channel_id]]
                else
                {
                    "videos_last_year": 0,
                    "last_video_date": ""
                }
            )
            for channel_id in channel_ids
        }

    def _get_subscriptions_stats(self):
        subscriptions = self._get_subscriptions()
        channel_ids = tuple(s["channel_id"] for s in subscriptions)

        channel_stats = self._get_channel_stats(channel_ids)

        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        one_year_ago = (today - timedelta(days=365)).isoformat()
        recent_video_stats = self._get_recent_video_stats(
            channel_ids, one_year_ago
        )

        result = []
        for s in subscriptions:
            result.append({
                "channel_id": s["channel_id"],
                "channel_title": s["channel_title"],
                "description": s["description"],
                "thumbnail": s["thumbnail"],
                **channel_stats[s["channel_id"]],
                **recent_video_stats[s["channel_id"]]
            })

        return result
    
    def _clean_text(self, text):
        text = re.sub(r"\s+", " ", text.strip())
        text = text[:77] + "..." if len(text) > 80 else text
        text = text.replace("|", r"\|")
        return text

    def _convert_stats_to_markdown(self, stats):
        headers = ["Thumbnail", "Channel", "Description", "Views", "Subscribers",
                   "Videos", "Videos/Year", "Last Video"]
        rows = [
            f"| {' | '.join(headers)} |",
            f"| {' | '.join(['---'] * len(headers))} |"
        ]

        for c in stats:
            try:
                last_video = datetime.fromisoformat(c["last_video_date"])
            except ValueError:
                last_video = datetime.fromtimestamp(0, tz=timezone.utc)
            delta = datetime.now(timezone.utc) - last_video
            days = delta.days
            if days == 0:
                relative = "Today"
            elif days < 7:
                relative = f"{days}d ago"
            elif days < 30:
                relative = f"{days // 7}w ago"
            elif days < 365:
                relative = f"{days // 30}mo ago"
            else:
                relative = f"{days // 365}y ago"

            thumbnail = f"![{c['channel_title']}]({c['thumbnail']})"
            desc = c["description"].replace("\n", " ")[:80] + "..."

            row = [
                thumbnail,
                self._clean_text(c['channel_title']),
                self._clean_text(desc),
                f"{c['view_count']:,}",
                f"{c['subscriber_count']:,}",
                str(c["video_count"]),
                str(c["videos_last_year"]),
                relative,
            ]
            rows.append(f"| {' | '.join(row)} |")

        return "\n".join(rows)

    def generate_subscriptions_report(self, out_file):
        stats = self._get_subscriptions_stats()
        markdown_text = self._convert_stats_to_markdown(stats)

        try:
            output_path = Path(out_file)
        except TypeError:
            logging.info(f"writing markdown report to stdout...")
            print(markdown_text)
            return

        logging.info(f"writing markdown report to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
