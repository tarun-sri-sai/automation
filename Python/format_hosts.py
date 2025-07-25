import sys


def parse_line(line: str) -> list[str]:
    """
    Parses a line from the hosts file and returns a Line object.
    """
    line = line.rstrip()
    cmt_idx = line.find("#")
    comment = line[cmt_idx:] if cmt_idx != -1 else ""
    columns = line[:cmt_idx].split() if cmt_idx != -1 else line.split()
    return [*columns, comment]


def next_multiple_of_4(n: int) -> int:
    """
    Finds the next multiple of 4 greater than or equal to n.
    """
    if n % 4 == 0:
        return n + 4

    return n + (4 - (n % 4))


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path_to_hosts_file>")
        sys.exit(1)

    hosts_file_path = sys.argv[1]
    try:
        with open(hosts_file_path, "r") as file:
            lines = file.read().split("\n")

        result = []
        for line in lines:
            result.append(parse_line(line))

        max_columns = max(len(line) for line in result)
        gaps = [0 for _ in range(max_columns)]
        for line in result:
            for i, word in enumerate(line):
                gaps[i] = max(gaps[i],
                              len(word) if not word.startswith("#") else 0)
        gaps = [next_multiple_of_4(gap) if gap > 0 else 0 for gap in gaps]

        for i, line in enumerate(result):
            final_string = "".join(f"{word:<{gaps[i]}}"
                                   for i, word in enumerate(line)).rstrip()
            result[i] = final_string

        with open(hosts_file_path, "w") as file:
            file.write("\n".join(result))
        print(f"Formatted {hosts_file_path} successfully.")
    except FileNotFoundError:
        print(f"Error: File '{hosts_file_path}' not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied to write to '{hosts_file_path}'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
