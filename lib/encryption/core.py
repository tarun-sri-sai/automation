import sys
from getpass import getpass


def read_password(prompt):
    if sys.stdin.isatty():
        return getpass(prompt)
    else:
        return sys.stdin.read().rstrip("\n")
