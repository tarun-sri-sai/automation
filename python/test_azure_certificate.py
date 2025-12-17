import msal
import hashlib
from argparse import ArgumentParser
from getpass import getpass
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates


def get_access_token(client_id, tenant_id, cert_path, cert_password, scope=None):
    scope = scope or "https://graph.microsoft.com/.default"

    with open(cert_path, "rb") as f:
        pfx_data = f.read()

    private_key, cert, additional_certs = load_key_and_certificates(
        pfx_data,
        cert_password.encode()
    )

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    pub_key = cert.public_bytes(
        serialization.Encoding.DER
    )
    thumbprint = hashlib.sha1(
        pub_key
    ).hexdigest()

    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential={
            "private_key": private_key_pem,
            "thumbprint": thumbprint,
        },
    )

    result = app.acquire_token_for_client(scopes=[scope])

    if "access_token" in result:
        return result["access_token"]
    else:
        raise ValueError(
            f"Failed to obtain token: {result.get('error_description', result)}"
        )


def main():
    parser = ArgumentParser(description="Test azure certificate")
    parser.add_argument("client_id", help="Azure app ID")
    parser.add_argument("tenant_id", help="Directory ID")
    parser.add_argument("cert_file",
                        help="Path to the certificate private key")

    args = parser.parse_args()

    cert_password = getpass(prompt="Enter the password to the private key: ")

    try:
        token = get_access_token(
            args.client_id,
            args.tenant_id,
            args.cert_file,
            cert_password
        )
        print(f"Azure app is correct. Token: {token}")
    except Exception as e:
        print(f"Azure app is invalid or credentials are incorrect. {e}")


if __name__ == '__main__':
    main()
