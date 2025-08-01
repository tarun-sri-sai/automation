import pyotp
import sys
import warnings
from argparse import ArgumentParser
from tabulate import tabulate
from getpass import getpass
from urllib.parse import urlparse, parse_qs, unquote
from lib.encryption import decrypt

# For warnings from cryptography
warnings.filterwarnings('ignore')


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
            password = getpass(
                "Enter the password to decrypt the encryption (OpenPGP): "
            )
            data = decrypt(data, password)

        return data.splitlines()
    except Exception as e:
        print(f"Error while decrypting TOTP urls from {file_path}: {e}")
        raise


def main():
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
        data = []
        for url in totp_urls:
            data.append(get_totp(url))

        print(tabulate(data, headers=headers, tablefmt="grid"))
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
