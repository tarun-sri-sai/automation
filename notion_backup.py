import json
import os
import requests
import sys
import time
from argparse import ArgumentParser
from tqdm import tqdm

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100
RATE_LIMIT_SLEEP = 30
MAX_RETRIES = 3

blocks_seen = set()


def _bar(iterable, **kwargs):
    return tqdm(iterable, file=sys.stderr, disable=None, **kwargs)


def _log(msg):
    tqdm.write(msg, file=sys.stderr)


class NotionClient:
    def __init__(self, token):
        self._blocks_seen = set()
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method, url, **kwargs):
        retry_count = 0
        while True:
            r = requests.request(
                method, url, headers=self._headers, **kwargs
            )
            if r.status_code == 429:
                wait_secs = int(r.headers.get("Retry-After"))
                _log(f"WARN\trate limited on {url}, waiting {wait_secs}s")
                time.sleep(wait_secs)
                continue

            if not (200 <= r.status_code < 300):
                _log(f"ERROR\t[{retry_count}] {url} response: {r.text}")

                retry_count += 1
                if retry_count == MAX_RETRIES:
                    sys.exit(1)

                time.sleep(RATE_LIMIT_SLEEP)

            return r.json()

    def _search_all(self):
        results = []
        payload = {"page_size": PAGE_SIZE}

        while True:
            data = self._request(
                "POST",
                "https://api.notion.com/v1/search",
                json=payload
            )
            results.extend(data["results"])

            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

        return results

    def _fetch_blocks(self, block_id, prevs=None, is_database=False):
        top_level = prevs is None and not is_database

        prevs = (prevs or 0) + 1

        if block_id in blocks_seen:
            _log(f"WARN\tduplicate request for {block_id}")

        blocks = []
        payload = {"page_size": PAGE_SIZE}

        while True:
            data = self._request(
                "GET",
                f"https://api.notion.com/v1/blocks/{block_id}/children",
                params=payload
            )

            blocks.extend(data["results"])

            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

        iterator = (
            _bar(
                blocks, desc=f" page {block_id}", unit="block",
                leave=False
            )
            if top_level else blocks
        )

        for block in iterator:
            if block.get("has_children"):
                block["children"] = self._fetch_blocks(block["id"], prevs)

        return blocks

    def _fetch_database_rows(self, database_id):
        rows = {}
        payload = {"page_size": PAGE_SIZE}

        full_data = []
        while True:
            data = self._request(
                "POST",
                f"https://api.notion.com/v1/databases/{database_id}/query",
                json=payload,
            )

            full_data += data["results"]

            if not data.get("has_more"):
                break

            payload["start_cursor"] = data["next_cursor"]

        for row in _bar(
            full_data, desc=f" database {database_id}", unit="row", leave=False
        ):
            row_id = row["id"]
            rows[row_id] = row
            rows[row_id]["blocks"] = self._fetch_blocks(row_id, is_database=True)

        return rows

    def backup(self):
        backup_data = {
            "pages": {},
            "databases": {}
        }

        _log("searching workspace...")
        objects = self._search_all()

        root_objects = [
            obj for obj in objects if obj["parent"]["type"] == "workspace"
        ]

        for obj in _bar(root_objects, desc="objects", unit="obj"):
            obj_id = obj["id"]

            if obj["object"] == "page":
                backup_data["pages"][obj_id] = obj
                backup_data["pages"][obj_id]["blocks"] = (
                    self._fetch_blocks(obj_id)
                )

            elif obj["object"] == "database":
                backup_data["databases"][obj_id] = {
                    "schema": obj,
                    "rows": self._fetch_database_rows(obj_id)
                }

        return backup_data


def main():
    parser = ArgumentParser(
        description="Backup Notion workspace to a JSON file"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output_backup.json",
        help="output file name (default: output_backup.json)"
    )
    parser.add_argument(
        "-t",
        "--token",
        default=os.environ.get("NOTION_TOKEN"),
        help="Notion API token (default: NOTION_TOKEN environment variable)"
    )
    args = parser.parse_args()

    backup_data = NotionClient(args.token).backup()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"backup complete -> {args.output}")


if __name__ == "__main__":
    main()
