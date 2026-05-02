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
        parser.add_argument(
            "-r",
            "--recipient",
            type=str,
            help="recipient to use for decryption (required if file is encrypted)"
        )
        args = parser.parse_args()

        totp_urls = get_totp_urls(args.file, args.encrypted, args.recipient)
        with Live(build_table(totp_urls), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(1)
                live.update(build_table(totp_urls))

    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")


if __name__ == "__main__":
    main()
