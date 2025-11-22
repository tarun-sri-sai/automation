from argparse import ArgumentParser
from getpass import getpass
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.runtime.http.request_options import RequestOptions
from cryptography.hazmat.primitives.serialization import (
    pkcs12,
    Encoding,
    PrivateFormat,
    NoEncryption
)
from cryptography.hazmat.backends import default_backend


def convert_pfx_to_pri_key(pfx_path, password):
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    private_key, _, _ = pkcs12.load_key_and_certificates(
        pfx_data, password.encode(), backend=default_backend()
    )

    return private_key.private_bytes(Encoding.PEM,
                                     PrivateFormat.TraditionalOpenSSL,
                                     NoEncryption())


def get_credential(client_id, tenant_id, certificate_file, thumbprint,
                   certificate_password):
    private_key = convert_pfx_to_pri_key(
        certificate_file,
        certificate_password
    )

    return {
        "tenant": tenant_id,
        "client_id": client_id,
        "thumbprint": thumbprint,
        "private_key": private_key,
    }


def main():
    parser = ArgumentParser(description="Test azure certificate")
    parser.add_argument("client_id", help="Azure app ID")
    parser.add_argument("tenant_id", help="Directory ID")
    parser.add_argument("certificate_file",
                        help="Path to the cert private key")
    parser.add_argument("thumbprint", help="Certificate thumbprint")
    parser.add_argument("site_url", help="Site URL")

    args = parser.parse_args()

    cert_password = getpass(prompt="Enter the password to the private key: ")

    try:
        credential = get_credential(client_id=args.client_id,
                                    tenant_id=args.tenant_id,
                                    certificate_file=args.certificate_file,
                                    thumbprint=args.thumbprint,
                                    certificate_password=cert_password)

        auth_context = AuthenticationContext(args.site_url)
        auth_context.with_client_certificate(
            tenant=args.tenant_id,
            client_id=args.client_id,
            private_key=credential.get("private_key"),
            thumbprint=credential.get("thumbprint"))

        full_url = "https://graph.microsoft.com/v1.0/organization"
        options = RequestOptions(full_url)
        options.set_header('Accept', 'application/json; odata=verbose')
        options.set_header('Content-Type', 'application/json')

        auth_context.authenticate_request(options)
        _ = options.headers["Authorization"]

        print("Azure app is valid")
    except Exception:
        print("Azure app is invalid or credentials are incorrect")


if __name__ == '__main__':
    main()
