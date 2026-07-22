import shutil
import subprocess
from pathlib import Path
from typing import Self
from lib.encryption.context import Context


class GnupgContext(Context):
    def __init__(self: Self, recipient: str) -> None:
        self._recipient = recipient

    def _is_gpg_available(self: Self) -> bool:
        if not shutil.which("gpg"):
            raise RuntimeError(
                "gpg is not available on this system. "
                "Please add it to PATH or install gpg"
            )

    def _run_gpg(self: Self, args: list[str], input: bytes = None) -> bytes:
        result = subprocess.run(
            ["gpg", "--yes", *args],
            input=input,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"gpg command failed: {stderr}")
        return result.stdout

    def decrypt(self: Self, encrypted_blob: bytes) -> bytes:
        self._is_gpg_available()
        return self._run_gpg(
            ["--decrypt", "--recipient", self._recipient, "-"],
            input=encrypted_blob
        )

    def encrypt_to_file(self: Self, plain: bytes, file: Path) -> bytes:
        self._is_gpg_available()
        return self._run_gpg(
            [
                "--encrypt",
                "--armor",
                "--recipient",
                self._recipient,
                "--output",
                file,
                "-"
            ],
            input=plain
        )
