import time
from argparse import ArgumentParser
from rich.console import Console
from rich.live import Live
from lib.totp import get_totp_urls, build_table


def main():
    console = Console()

    try:
        parser = ArgumentParser(
            description="Generates TOTP on the fly from a TOTP export file"
        )
        parser.add_argument(
            "file",
            help="Path to the export file"
        )
        parser.add_argument(
            "-e",
            "--encrypted",
            dest="encrypted",
            action="store_true",
            help="Whether the file is encrypted (OpenPGP)"
        )
        args = parser.parse_args()

        totp_urls = get_totp_urls(args.file, args.encrypted)
        with Live(build_table(totp_urls), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(1)
                live.update(build_table(totp_urls))

    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")


if __name__ == "__main__":
    main()
