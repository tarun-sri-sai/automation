from argparse import ArgumentParser
from rich.console import Console
from lib.encryption import GnupgContext, ProtonAuthenticatorExportV1Context
from lib.encryption.core import read_password
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

    parser.add_argument(
        "-r",
        "--raw",
        action="store_true"
    )

    args = parser.parse_args()

    ctx = None
    if args.encryption_type == "gnupg":
        ctx = GnupgContext(args.gnupg_recipient)
    elif args.encryption_type == "proton_authenticator_export_v1":
        password = read_password(
            "enter password for proton authenticator export v1: "
        )
        ctx = ProtonAuthenticatorExportV1Context(password)

    console = Console()
    totp_urls = get_totp_urls(args.file, ctx)

    if args.raw:
        print("\n".join(totp_urls))
        return

    console.print(build_table(totp_urls, raw=True))


if __name__ == "__main__":
    main()
