import time
from argparse import ArgumentParser
from pathlib import Path
from rich.console import Console
from rich.live import Live
from lib.encryption.gnupg.context import GnupgContext
from lib.totp.parse import get_totp_urls, build_table


def main() -> None:
    console = Console()

    try:
        parser = ArgumentParser(
            description="Generates TOTP on the fly from a TOTP export file"
        )
        parser.add_argument(
            "file",
            type=Path,
            help="Path to the export file"
        )

        parser.add_argument(
            "-e",
            "--encryption-type",
            type=str,
            help="encryption used for the credentials"
        )
        parser.add_argument(
            "--gnupg-recipient",
            type=str,
            help="gnupg recipient to use for decryption and encryption"
        )

        args = parser.parse_args()

        ctx = None
        if args.encryption_type == "gnupg":
            ctx = GnupgContext(args.gnupg_recipient)

        totp_urls = get_totp_urls(args.file, ctx)
        with Live(
            build_table(totp_urls), refresh_per_second=1, console=console
        ) as live:
            while True:
                time.sleep(1)
                live.update(build_table(totp_urls))

    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")


if __name__ == "__main__":
    main()
