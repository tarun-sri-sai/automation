from argparse import ArgumentParser
from rich.console import Console
from lib.totp import get_totp_urls, build_table


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
        "--encrypted",
        dest="encrypted",
        action="store_true",
        help="Whether the file is encrypted (OpenPGP)"
    )
    args = parser.parse_args()

    totp_urls = get_totp_urls(args.file, args.encrypted)

    console = Console()
    console.print(build_table(totp_urls, raw=True))


if __name__ == "__main__":
    main()
