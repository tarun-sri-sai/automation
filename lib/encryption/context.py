from abc import ABC, abstractmethod
from pathlib import Path
from typing import Self


class Context(ABC):
    @abstractmethod
    def decrypt(self: Self, encrypted_blob: bytes) -> bytes:
        pass

    @abstractmethod
    def encrypt_to_file(self: Self, plain: bytes, file: Path) -> None:
        pass
