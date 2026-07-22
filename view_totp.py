from argparse import ArgumentParser
from rich.console import Console
from lib.encryption.gnupg.context import GnupgContext
from lib.totp.parse import get_totp_urls, build_table


def main():
    parser = ArgumentParser(
        description="Generates TOTP on the fly from a TOTP export file"
    )
    parser.add_argument(
        "file",
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

    console = Console()
    totp_urls = get_totp_urls(args.file, ctx)
    console.print(build_table(totp_urls, raw=True))


if __name__ == "__main__":
    main()
