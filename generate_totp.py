import pyotp
import time
import yaml
from argparse import ArgumentParser
from lib.encryption import decrypt, read_password
from rich.console import Console
from rich.live import Live
from rich.table import Table
from urllib.parse import urlparse, parse_qs, unquote


def parse_otpauth_url(otpauth_url):
    o = urlparse(otpauth_url)

    # Example path: '/<Issuer>:<Username>@<Domain>'
    label = o.path[1:]  # Remove leading slash
    if ':' in label:
        issuer_in_label, email = label.split(':', 1)
    else:
        issuer_in_label, email = None, label

    params = parse_qs(o.query)
    secret = params.get('secret', [None])[0]
    issuer = params.get('issuer', [issuer_in_label])[0]

    # Decode in case of percent-encoding
    email = unquote(email) if email else None
    issuer = unquote(issuer) if issuer else None

    return issuer, email, secret


def get_totp(totp_url):
    try:
        issuer, email, secret = parse_otpauth_url(totp_url)

        totp = pyotp.TOTP(secret)
        code = totp.now()

        return issuer, email, code
    except Exception as e:
        print(f"Failed to get TOTP: {e}")
        raise


def get_totp_urls(file_path, encrypted):
    try:
        with open(file_path, "r") as f:
            data = f.read()

        if encrypted:
            password = read_password(
                "Enter the password to decrypt the encryption (OpenPGP): "
            )
            data = yaml.safe_load(decrypt(data, password))

        return data["Secret URIs"]
    except Exception as e:
        print(f"Error while decrypting TOTP urls from {file_path}: {e}")
        raise


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

        headers = ["Issuer", "Email", "TOTP"]

        def build_table():
            table = Table(show_header=True, header_style="bold cyan")

            for col in headers:
                table.add_column(col)

            for url in totp_urls:
                issuer, email, totp = get_totp(url)
                table.add_row(issuer, email, totp)

            return table

        with Live(build_table(), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(15)
                live.update(build_table())

    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")


if __name__ == "__main__":
    main()
