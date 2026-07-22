import logging
from argparse import ArgumentParser
from pathlib import Path
from lib.forge.factory import Factory
from lib.logging_util import setup_logger


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


def main():
    init_logger()

    parser = ArgumentParser(
        description="checks the branch protections for all repos in a forge"
    )
    parser.add_argument(
        "forge",
        type=str,
        help="name of the forge to check branch protections for"
    )
    args = parser.parse_args()

    try:
        Factory(args.forge).build_branch_protections().verify()
    except Exception as e:
        logging.critical(
            f"error verifying branch protections: {e}", exc_info=True)


if __name__ == '__main__':
    main()
