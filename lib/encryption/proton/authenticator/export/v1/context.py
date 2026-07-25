import json
import secrets
from argon2.low_level import hash_secret_raw, Type
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path
from typing import Self
from lib.encryption.context import Context


class ProtonAuthenticatorExportV1Context(Context):
    def __init__(self: Self, password: str) -> None:
        self._password = password
        self._ASSOCIATED_DATA = b"proton.authenticator.export.v1"

    def decrypt(self: Self, encrypted_blob: bytes) -> bytes:
        json_data = json.load(encrypted_blob.decode())
        salt = b64decode(json_data["salt"])
        key = hash_secret_raw(
            secret=self._password, salt=salt, time_cost=2, 
            memory_cost=19 * 1024, parallelism=1, hash_len=32, type=Type.ID
        )

        content = b64decode(json_data["content"])
        iv = content[:12]
        ciphertext = content[12:]
        associated_data = self._ASSOCIATED_DATA

        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext, associated_data)

    def encrypt_to_file(self: Self, plain: bytes, file: Path) -> None:
        salt = secrets.token_bytes(16)

        key = hash_secret_raw(
            secret=self._password, salt=salt, time_cost=2, 
            memory_cost=19 * 1024, parallelism=1, hash_len=32, type=Type.ID
        )

        iv = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plain, self._ASSOCIATED_DATA)

        data = {
            "version": 1,
            "salt": b64encode(salt).decode(),
            "content": b64encode(iv + ciphertext).decode(),
        }

        file.write_text(json.dumps(data))
