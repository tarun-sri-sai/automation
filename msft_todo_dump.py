#!/usr/bin/env python3
"""Backup Microsoft To Do to a SQLite dump via the Microsoft Graph API.

Fetches the signed-in user's To Do task lists, tasks, file attachments and
checklist items from Microsoft Graph, stores them in an in-memory SQLite
database (schema from msft_todo_dump.sql) and writes a full SQL dump of that
in-memory database to a file (default: todo_dump.sql).

Authentication uses the MSAL public client flow (device code). The access
and refresh tokens are persisted in msft_todo_credential.json, so subsequent
runs can acquire a fresh token silently without re-authenticating.

Usage:
    python3 todo_dump.py [client_id] [-o OUTPUT] [--cache FILE]

The client ID is taken from the command line, or from the
AZURE_APP_CLIENT_ID environment variable.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import msal
import requests

# Public client flow for personal Microsoft accounts, as in msal_auth.py
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Tasks.ReadWrite"]
GRAPH_TODO_BASE = "https://graph.microsoft.com/v1.0/me/todo"

DEFAULT_OUTPUT = "todo_dump.sql"
DEFAULT_CACHE_FILE = "msft_todo_credential.json"
DEFAULT_MIGRATION_FILE = Path(__file__).resolve().with_name(
    "msft_todo_dump.sql"
)


# ---------------------------------------------------------------------------
# Token cache / authentication
# ---------------------------------------------------------------------------

def load_token_cache(path: Path) -> msal.SerializableTokenCache:
    """
    Load the persisted MSAL token cache (access/refresh tokens) if present.
    """
    cache = msal.SerializableTokenCache()
    if path.exists():
        try:
            cache.deserialize(path.read_text(encoding="utf-8"))
        except Exception:
            print(
                (
                    f"warning: could not read token cache from {path}, " +
                    f"starting fresh"
                ), file=sys.stderr
            )
            cache = msal.SerializableTokenCache()
    return cache


def save_token_cache(cache: msal.SerializableTokenCache, path: Path) -> None:
    """
    Persist the MSAL token cache so the next run can authenticate silently.
    """
    path.write_text(cache.serialize(), encoding="utf-8")


def acquire_token(client_id: str, cache: msal.SerializableTokenCache) -> str:
    """
    Get an access token silently if possible, otherwise via device code flow.
    """
    app = msal.PublicClientApplication(
        client_id, authority=AUTHORITY, token_cache=cache
    )

    # Try the cached accounts first (refresh token / cached access token).
    for account in app.get_accounts():
        result = app.acquire_token_silent(SCOPES, account=account)
        if result and "access_token" in result:
            print(
                f"Authenticated silently as " +
                f"{account['username'] or account.get('local_account_id')}"
            )
            return result["access_token"]

    # No usable cached token: fall back to the device code flow.
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        sys.exit(
            f"device flow failed to start: " +
            f"{flow.get('error_description', flow)}"
        )
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        sys.exit(
            f"device flow failed: {result.get('error_description', result)}"
        )
    return result["access_token"]


# ---------------------------------------------------------------------------
# Microsoft Graph helpers
# ---------------------------------------------------------------------------

def graph_get(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def graph_get_all(session: requests.Session, url: str) -> list:
    """GET a collection endpoint, following @odata.nextLink pagination."""
    entities = []
    while url:
        payload = graph_get(session, url)
        entities.extend(payload.get("value", []))
        url = payload.get("@odata.nextLink")
    return entities


def strip_odata(obj):
    """Recursively drop @odata.* fields from a Graph JSON payload."""
    if isinstance(obj, dict):
        return {
            k: strip_odata(v)
            for k, v in obj.items()
            if not k.startswith("@odata.")
        }
    if isinstance(obj, list):
        return [strip_odata(item) for item in obj]
    return obj


def json_value(entity: dict) -> str:
    """
    Serialize an entity for the `value` column (JSON without @odata.* fields).
    """
    return json.dumps(strip_odata(entity), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def build_database(migration_sql: str) -> sqlite3.Connection:
    """Create the in-memory SQLite database and apply the migration schema."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(migration_sql)
    return conn


def insert_entity(
    conn: sqlite3.Connection, table: str, entity_id: str, value: str
) -> None:
    conn.execute(
        f"INSERT OR REPLACE INTO {table} (id, value) VALUES (?, ?)",
        (entity_id, value),
    )


def fetch_and_store(
    session: requests.Session, conn: sqlite3.Connection
) -> dict:
    """Fetch To Do data from Graph and insert rows into the in-memory DB."""
    stats = {
        "lists": 0,
        "tasks": 0,
        "attachments": 0,
        "checklist_items": 0,
        "list_task_links": 0,
        "task_attachment_links": 0,
        "task_checklist_links": 0
    }

    lists = graph_get_all(session, f"{GRAPH_TODO_BASE}/lists")
    for lst in lists:
        list_id = lst["id"]
        insert_entity(conn, "todo_task_lists", list_id, json_value(lst))
        stats["lists"] += 1

        print(f"task list: {lst.get('displayName', '<unnamed>')} ({list_id})")

        TASKS_BASE = f"{GRAPH_TODO_BASE}/lists/{list_id}/tasks"
        for task in graph_get_all(session, TASKS_BASE):
            task_id = task["id"]
            insert_entity(conn, "todo_tasks", task_id, json_value(task))
            stats["tasks"] += 1

            cur = conn.execute(
                (
                    "INSERT OR IGNORE INTO todo_task_list_tasks (" +
                    "todo_task_list_id, todo_task_id) VALUES (?, ?)"
                ),
                (list_id, task_id),
            )
            stats["list_task_links"] += cur.rowcount

            for item in graph_get_all(
                session, f"{TASKS_BASE}/{task_id}/checklistItems"
            ):
                item_id = item["id"]
                insert_entity(conn, "todo_checklist_items",
                              item_id, json_value(item))
                stats["checklist_items"] += 1

                cur = conn.execute(
                    "INSERT OR IGNORE INTO todo_task_checklist_items "
                    "(todo_task_id, task_checklist_item_id) VALUES (?, ?)",
                    (task_id, item_id),
                )
                stats["task_checklist_links"] += cur.rowcount

            for attachment in graph_get_all(
                session, f"{TASKS_BASE}/{task_id}/attachments"
            ):
                attachment_id = attachment["id"]
                insert_entity(conn, "todo_file_attachments",
                              attachment_id, json_value(attachment))
                stats["attachments"] += 1

                cur = conn.execute(
                    "INSERT OR IGNORE INTO todo_task_file_attachments "
                    "(todo_task_id, task_file_attachment_id) VALUES (?, ?)",
                    (task_id, attachment_id),
                )
                stats["task_attachment_links"] += cur.rowcount

    conn.commit()
    return stats


def dump_database(conn: sqlite3.Connection, output_path: Path) -> None:
    """Write a full SQL dump of the in-memory database to output_path."""
    with open(output_path, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(line + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dump Microsoft To Do (lists, tasks, attachments, checklist " +
            "items) into an in-memory SQLite DB and write the DB dump to a " +
            ".sql file."
        )
    )
    parser.add_argument(
        "client_id",
        nargs="?",
        help=(
            "Azure App Registration client ID (falls back to the " +
            "AZURE_APP_CLIENT_ID environment variable)"
        ),
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        help=(
            f"path of the SQL dump file to create (default: " +
            f"{DEFAULT_OUTPUT})"
        ),
    )
    parser.add_argument(
        "--cache",
        default=DEFAULT_CACHE_FILE,
        help=(
            f"path of the MSAL token cache file (default: " +
            f"{DEFAULT_CACHE_FILE})"
        ),
    )
    parser.add_argument(
        "--migration",
        default=str(DEFAULT_MIGRATION_FILE),
        help=(
            f"path of the migration SQL file (default: " +
            f"{DEFAULT_MIGRATION_FILE})"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list | None = None) -> None:
    args = parse_args(argv)

    client_id = args.client_id or os.environ.get(
        "AZURE_APP_CLIENT_ID", ""
    ).strip()
    if not client_id:
        sys.exit("no client ID provided (argument or AZURE_APP_CLIENT_ID)")

    # --- authenticate (silent token refresh when possible) ---
    cache_path = Path(args.cache)
    cache = load_token_cache(cache_path)
    token = acquire_token(client_id, cache)
    save_token_cache(cache, cache_path)

    # --- build the in-memory DB from the migration ---
    migration_path = Path(args.migration)
    if not migration_path.exists():
        sys.exit(f"migration file not found: {migration_path}")
    conn = build_database(migration_path.read_text(encoding="utf-8"))

    # --- fetch To Do data and insert rows ---
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    stats = fetch_and_store(session, conn)

    # --- dump the in-memory DB to the output file ---
    output_path = Path(args.output)
    dump_database(conn, output_path)

    print(
        f"done: {stats['lists']} task lists, {stats['tasks']} tasks, " +
        f"{stats['attachments']} file attachments, " +
        f"{stats['checklist_items']} checklist items"
    )
    print(f"dump written to {output_path}")


if __name__ == "__main__":
    main()
