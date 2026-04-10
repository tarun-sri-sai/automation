import sys
import shutil
import subprocess
from getpass import getpass


def _run_gpg(args, input=None) -> bytes:
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


def _is_gpg_available() -> bool:
    if not shutil.which("gpg"):
        raise RuntimeError(
            "gpg is not available on this system. "
            "Please add it to PATH or install gpg"
        )


def decrypt(encrypted_blob: bytes, recipient: str) -> bytes:
    _is_gpg_available()
    return _run_gpg(["--decrypt", "--recipient", recipient, "-"], input=encrypted_blob)


def encrypt(plaintext: str, file_path: str, recipient: str) -> bytes:
    _is_gpg_available()
    _run_gpg(
        ["--encrypt", "--armor", "--recipient", recipient, "--output", file_path, "-"], 
        input=plaintext.encode("utf-8")
    )


def read_password(prompt):
    if sys.stdin.isatty():
        return getpass(prompt)
    else:
        return sys.stdin.read().rstrip("\n")
