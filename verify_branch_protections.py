import logging
from argparse import ArgumentParser
from pathlib import Path
from lib.forge.gitea.branch_protections import GiteaBranchProtections
from lib.logging_util import setup_logger

branch_protections = {
    "gitea": GiteaBranchProtections
}


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
        help=(
            f"name of the forge (values: {list(branch_protections.keys())})"
        )
    )
    args = parser.parse_args()

    try:
        branch_protections[args.forge].verify()
    except Exception as e:
        logging.critical(f"error verifying branch protections: {e}", exc_info=True)


if __name__ == '__main__':
    main()
