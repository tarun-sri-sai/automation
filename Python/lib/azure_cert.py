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
