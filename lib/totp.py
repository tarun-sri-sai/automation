import pyotp
from rich.table import Table
from urllib.parse import urlparse, parse_qs, unquote
from lib.encryption import decrypt, read_password


def get_totp_urls(file_path, encrypted):
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        if encrypted:
            password = read_password("password: ")
            data = decrypt(data, password)
        
        return [l.strip() for l in data.split("\n") if l.strip()]
    except Exception as e:
        print(f"Error while decrypting TOTP urls from {file_path}: {e}")
        raise


def _parse_otpauth_url(otpauth_url):
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


def _get_totp(totp_url, raw=False):
    try:
        issuer, email, secret = _parse_otpauth_url(totp_url)

        if raw:
            return issuer, email, secret

        totp = pyotp.TOTP(secret)
        code = totp.now()

        return issuer, email, code
    except Exception as e:
        print(f"Failed to get TOTP: {e}")
        raise


def build_table(totp_urls, headers=["Issuer", "Email", "TOTP"], raw=False):
    table = Table(show_header=True, header_style="bold cyan")

    for col in headers:
        table.add_column(col)

    for url in totp_urls:
        issuer, email, totp = _get_totp(url, raw=raw)
        table.add_row(issuer, email, totp)

    return table
