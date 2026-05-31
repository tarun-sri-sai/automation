import json
import logging
from argparse import ArgumentParser
from pathlib import Path
from lib.encryption import read_password
from lib.logging_util import setup_logger
from lib.google.youtube.context import YouTubeContext


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
        "-o", "--output", type=str, default="output.json",
        help="output file name (default: output.json)"
    )
    args = parser.parse_args()

    yt = YouTubeContext(
        args.client_id, read_password("client secret: "), args.project_id
    )
    subscriptions = yt.get_subscriptions()
    stats = yt.get_channel_stats(
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
                "video_count": stats[s["channel_id"]]["video_count"],
                "thumbnail": s["thumbnail"]
            }
            for s in subscriptions
        ], f, indent=2)

    logging.info(f"done! output written to {output_path}")


if __name__ == "__main__":
    main()
