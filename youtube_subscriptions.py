import json
import logging
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from lib.encryption import read_password
from lib.logging_util import setup_logger
from lib.private.google.youtube.context import YouTubeContext


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")


def main():
    init_logger()

    parser = ArgumentParser(
        description="create report on youtube subscriptions"
    )
    parser.add_argument(
        "client_id", type=str, help="oauth2 client ID"
    )
    parser.add_argument(
        "project_id", type=str, help="project ID"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="output file name"
    )
    args = parser.parse_args()

    yt = YouTubeContext(
        args.client_id, read_password("client secret: "), args.project_id
    )

    yt.generate_subscriptions_report(args.output)


if __name__ == "__main__":
    main()
