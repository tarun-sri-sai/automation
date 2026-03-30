import json
import sys
from argparse import ArgumentParser
from lib.todo import parse_todo


def get_text():
    parser = ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        help="path to the todo file",
        type=str
    )
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r") as f:
                return f.read()
        except Exception:
            print(f"failed to read file: {args.file}", file=sys.stderr)
            sys.exit(1)

    result = ""
    while True:
        try:
            line = input()
            result.join(line + "\n")
        except EOFError:
            break

    return result


def main():
    try:
        text = get_text()
        output = json.dumps(parse_todo(text))
        print(output)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
