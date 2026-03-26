import json
import re
import sys
from argparse import ArgumentParser
from hashlib import sha256


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


def normalize_newlines(text):
    return re.sub(r"\r\n", "\n", text.strip())


def split_blocks(text):
    text_blocks = re.split(r"\n[\n\s]*\n", text)
    return [block.split("\n") for block in text_blocks]


def is_heading_block(block):
    if len(block) != 3 or len(block[0]) != 32 or block[0][0] != "*":
        return False

    start = set(block[0])
    end = set(block[-1])

    return (
        all(l == l.lstrip() and l for l in block) and
        len(start) == len(end) == 1 and
        start == end and
        len(block[0]) == len(block[-1])
    )


def is_finished(block):
    return len(block) >= 2 and bool(re.match(r"^\[DONE\].*$", block[-1]))


def parse_blocks(blocks):
    block_data = []
    for block in blocks:
        if is_heading_block(block):
            block_data.append({
                "heading": block[1],
                "id": sha256(block[1].encode()).hexdigest()[:8]
            })
            continue

        curr_indent = None
        block_lines = []

        for line in block:
            indent_matches = re.match(r"^((?: {4})*)\S.*$", line)
            if not indent_matches:
                print(
                    f"invalid indentation for \"{line}\"",
                    file=sys.stderr
                )
                sys.exit(1)

            indent = indent_matches.group(1)
            if (
                curr_indent is not None and
                indent != curr_indent
            ):
                print(
                    f"inconsistent indentation for \"{line}\"",
                    file=sys.stderr
                )
                sys.exit(1)

            if curr_indent is None:
                curr_indent = indent

            block_lines.append(line.strip())

        block_data.append({
            "indent": len(curr_indent) // 4,
            "lines": block_lines,
            "id": sha256(block_lines[0].encode()).hexdigest()[:8],
            "finished": is_finished(block_lines)
        })

    return block_data


def validate_parents(block_data):
    curr_indents = [-1]
    curr_heading = ""
    blocks_since_heading = 0
    for block in block_data:
        if "heading" in block:
            blocks_since_heading = 0
            curr_indents = [-1]
            curr_heading = block["heading"]
            continue

        if blocks_since_heading == 0:
            if block.get("indent") > 0:
                print(f"invalid first task for {curr_heading}", file=sys.stderr)
                sys.exit(1)

            curr_indents.append(0)
            blocks_since_heading += 1
            continue

        while curr_indents and curr_indents[-1] > block["indent"]:
            curr_indents.pop()

        if (
            block["indent"] != curr_indents[-1] and 
            block["indent"] - 1 != curr_indents[-1]
        ):
            print(
                f"invalid parent task for \"{block['lines'][0]}\"",
                file=sys.stderr
            )
            sys.exit(1)

        if block["indent"] == curr_indents[-1] + 1:
            curr_indents.append(block["indent"])

        blocks_since_heading += 1


def validate_block_data(block_data):
    if len(block_data) == 0:
        print("empty todo", file=sys.stderr)
        sys.exit(0)

    if "heading" not in block_data[0]:
        print("first block must be a heading", file=sys.stderr)
        sys.exit(1)

    validate_parents(block_data)

def parse_todo(text):
    blocks = split_blocks(text)

    block_data = parse_blocks(blocks)
    validate_block_data(block_data)

    return block_data


def main():
    try:
        text = normalize_newlines(get_text())
        output = json.dumps(parse_todo(text))
        print(output)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
