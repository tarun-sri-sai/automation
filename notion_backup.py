import json
import os
import requests
import sys
import time
from argparse import ArgumentParser

NOTION_VERSION = "2022-06-28"
PAGE_SIZE = 100
RATE_LIMIT_SLEEP = 0.35


blocks_seen = set()


class NotionClient:
    def __init__(self, token):
        self._blocks_seen = set()
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method, url, payload=None):
        while True:
            r = requests.request(
                method, url, headers=self._headers, json=payload
            )
            if r.status_code == 429:
                print(
                    (
                        f"WARN\trate limited on {url}, waiting " +
                        f"{RATE_LIMIT_SLEEP * 10}s"
                    ),
                    file=sys.stderr
                )
                time.sleep(RATE_LIMIT_SLEEP * 10)
                continue

            if r.status_code != 200:
                print(f"ERROR\t{url} response: {r.text}", file=sys.stderr)
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
                payload
            )
            results.extend(data["results"])

            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

        return results


    def _fetch_blocks(self, block_id, prevs=None):
        prevs = (prevs or 0) + 1

        print("    " * (prevs - 1) + " |- " + block_id)

        if block_id in blocks_seen:
            print(f"WARN\tduplicate request for {block_id}", file=sys.stderr)

        blocks = []
        cursor = None

        while True:
            url = (
                f"https://api.notion.com/v1/blocks/{block_id}"
                f"/children?page_size={PAGE_SIZE}"
            )
            if cursor:
                url += f"&start_cursor={cursor}"

            data = self._request("GET", url)
            blocks.extend(data["results"])

            if not data.get("has_more"):
                break
            cursor = data["next_cursor"]

        for block in blocks:
            if block.get("has_children"):
                block["children"] = self._fetch_blocks(block["id"], prevs)

        return blocks


    def _fetch_database_rows(self, database_id):
        rows = {}
        payload = {"page_size": PAGE_SIZE}

        while True:
            data = self._request(
                "POST",
                f"https://api.notion.com/v1/databases/{database_id}/query",
                payload,
            )

            for row in data["results"]:
                row_id = row["id"]
                rows[row_id] = row
                rows[row_id]["blocks"] = self._fetch_blocks(row_id)

            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

        return rows

    def backup(self):
        backup_data = {
            "pages": {},
            "databases": {}
        }

        print("searching workspace...")
        objects = self._search_all()

        for obj in objects:
            obj_id = obj["id"]

            # this prevents retrieval duplication
            if obj["parent"]["type"] != "workspace":
                print(
                    f"DEBUG\tskipping non-root object: {obj_id}",
                    file=sys.stderr
                )
                continue

            if obj["object"] == "page":
                print(f"page: {obj_id}")
                backup_data["pages"][obj_id] = obj
                backup_data["pages"][obj_id]["blocks"] = (
                    self._fetch_blocks(obj_id)
                )

            elif obj["object"] == "database":
                print(f"database: {obj_id}")
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

    print(f"\nbackup complete -> {args.output}")


if __name__ == "__main__":
    main()
