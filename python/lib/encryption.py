from pgpy import PGPMessage


def decrypt(encrypted_blob: bytes, password: str) -> bytes:
    message = PGPMessage.from_blob(encrypted_blob)
    return message.decrypt(password).message
