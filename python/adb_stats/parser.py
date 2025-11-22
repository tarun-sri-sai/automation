import pandas as pd
import re
import sys
from pathlib import Path


def parse_line_into_pairs(line):
    pattern = re.compile(r'(\w+)=(?:"((?:[^"\\]|\\.)*)"|([^\s]+))', re.VERBOSE)

    result = {}
    for match in pattern.finditer(line):
        key = match.group(1)
        value = (
            match.group(2)
            if match.group(2) is not None
            else match.group(3)
        )
        if value is not None:
            value = value.replace(r'\"', '"')
        result[key] = value
    return result


def convert_to_records(text):
    records = []
    for line in text.splitlines():
        line = line.strip()
        records.append(parse_line_into_pairs(line))
    return records


def main():
    if len(sys.argv) != 2:
        print("Usage: python parser.py <input_file>")
        sys.exit(1)

    file = sys.argv[1]
    with open(file, "r") as f:
        dataframe = pd.DataFrame(convert_to_records(f.read()))
        dataframe.to_csv(f"{Path(file).stem}.csv", index=False)


if __name__ == '__main__':
    main()
