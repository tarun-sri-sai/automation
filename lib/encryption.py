import sys
from pgpy import PGPMessage
from getpass import getpass


def decrypt(encrypted_blob: bytes, password: str) -> bytes:
    message = PGPMessage.from_blob(encrypted_blob)
    return message.decrypt(password).message


def encrypt(plaintext: bytes, password: str) -> bytes:
    message = PGPMessage.new(plaintext)
    encrypted_message = message.encrypt(password)
    return bytes(str(encrypted_message), encoding='utf-8')


def read_password(prompt):
    if sys.stdin.isatty():
        return getpass(prompt)
    else:
        return sys.stdin.read().rstrip("\n")
