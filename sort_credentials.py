import sys
from argparse import ArgumentParser
from io import StringIO
from pathlib import Path
from ruamel.yaml import YAML
from typing import Any
from lib.encryption.context import Context
from lib.encryption.gnupg.context import GnupgContext


def _rec_sort(d: Any) -> Any:
    if isinstance(d, dict):
        res = dict()
        for k in sorted(d.keys()):
            res[k] = _rec_sort(d[k])
        return res
    if isinstance(d, list):
        for idx, elem in enumerate(d):
            d[idx] = _rec_sort(elem)
    return d


def _walk_credentials(
    parent_path: Path, ctx: Context, pattern: str | None = None
) -> None:
    if not pattern:
        pattern = "*"

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=4, sequence=4, offset=4)

    files = [f for f in parent_path.rglob(pattern) if f.is_file()]
    for file in files:
        try:
            with open(file, "rb") as f:
                contents = ctx.decrypt(f.read()).decode("utf-8")

            sorted_data = _rec_sort(yaml.load(contents))
            stream = StringIO()
            yaml.dump(sorted_data, stream)
            sorted_contents = stream.getvalue()

            if contents.replace("\r", "") != sorted_contents:
                print(f"{file} needs to be sorted")

                ctx.encrypt_to_file(sorted_contents.encode(), file)

        except AttributeError:
            print(f"{file} is not valid yaml", file=sys.stderr)
        except Exception as e:
            print(f"error while trying to sort {file} as yaml: {e}")


def main() -> None:
    parser = ArgumentParser(description="sort yaml credentials")

    parser.add_argument(
        "directory",
        type=Path,
        help="directory containing credential files"
    )
    parser.add_argument("-f", "--filter", help="glob pattern to match files")

    parser.add_argument(
        "-e",
        "--encryption-type",
        type=str,
        help="encryption used for the credentials"
    )
    parser.add_argument(
        "--gnupg-recipient",
        type=str,
        help="gnupg recipient to use for decryption and encryption"
    )

    args = parser.parse_args()

    ctx = None
    if args.encryption_type == "gnupg":
        ctx = GnupgContext(args.gnupg_recipient)
    else:
        raise ValueError(f"unsupported encryption type {args.encryption_type}")

    _walk_credentials(args.directory, ctx, args.filter)


if __name__ == '__main__':
    main()
