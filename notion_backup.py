import os
import sys
import json
import time
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
OUTPUT_FILE = "notion_backup.json"
PAGE_SIZE = 100
RATE_LIMIT_SLEEP = 0.35

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

blocks_seen = set()


def notion_request(method, url, payload=None):
    while True:
        r = requests.request(method, url, headers=HEADERS, json=payload)
        if r.status_code == 429:
            print(f"WARN\trate limited on {url}, waiting {RATE_LIMIT_SLEEP * 10}s", file=sys.stderr)
            time.sleep(RATE_LIMIT_SLEEP * 10)
            continue

        if r.status_code != 200:
            print(f"ERROR\t{url} response: {r.text}", file=sys.stderr)
            sys.exit(1)

        time.sleep(RATE_LIMIT_SLEEP)
        return r.json()


def search_all():
    results = []
    payload = {"page_size": PAGE_SIZE}

    while True:
        data = notion_request(
            "POST",
            "https://api.notion.com/v1/search",
            payload
        )
        results.extend(data["results"])

        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    return results


def fetch_blocks(block_id, prevs=None):
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

        data = notion_request("GET", url)
        blocks.extend(data["results"])

        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]

    # recurse into children
    for block in blocks:
        if block.get("has_children"):
            block["children"] = fetch_blocks(block["id"], prevs)

    return blocks


def fetch_database_rows(database_id):
    rows = {}
    payload = {"page_size": PAGE_SIZE}

    while True:
        data = notion_request(
            "POST",
            f"https://api.notion.com/v1/databases/{database_id}/query",
            payload,
        )

        for row in data["results"]:
            row_id = row["id"]
            rows[row_id] = row
            rows[row_id]["blocks"] = fetch_blocks(row_id)

        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    return rows


def main():
    backup_data = {
        "pages": {},
        "databases": {}
    }

    print("searching workspace...")
    objects = search_all()

    for obj in objects:
        obj_id = obj["id"]

        # this prevents retrieval duplication
        if obj["parent"]["type"] != "workspace":
            print(f"DEBUG\tskipping non-root object: {obj_id}", file=sys.stderr)
            continue

        if obj["object"] == "page":
            print(f"page: {obj_id}")
            backup_data["pages"][obj_id] = obj
            backup_data["pages"][obj_id]["blocks"] = fetch_blocks(obj_id)

        elif obj["object"] == "database":
            print(f"database: {obj_id}")
            backup_data["databases"][obj_id] = {
                "schema": obj,
                "rows": fetch_database_rows(obj_id)
            }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"\nbackup complete -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
