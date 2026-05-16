import secrets
from argparse import ArgumentParser


def main():
    excluded = {
        ord('"'),
        ord("$"),
        ord("%"),
        ord("'"),
        ord("0"),
        ord("1"),
        ord("I"),
        ord("O"),
        ord("\\"),
        ord("l"),
        ord("|")
    }
    password_eligible = tuple(i for i in range(33, 127) if i not in excluded)

    parser = ArgumentParser(
        description="Generates a random password of a specified length"
    )
    parser.add_argument(
        "length",
        type=int,
        help="The length of the password to generate"
    )
    args = parser.parse_args()

    password = "".join(
        chr(secrets.choice(password_eligible))
        for _ in range(args.length)
    )
    print(password)


if __name__ == "__main__":
    main()
