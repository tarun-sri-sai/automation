import os
import sys
from getpass import getpass


def read_password(prompt):
    PASSWORD_ENV_KEY = "PASSWORD"

    if os.environ.get(PASSWORD_ENV_KEY):
        return os.environ[PASSWORD_ENV_KEY]

    if sys.stdin.isatty():
        return getpass(prompt)
    else:
        return sys.stdin.read().rstrip("\n")
