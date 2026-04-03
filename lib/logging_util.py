import logging
import os
import sys
from logging import handlers


def setup_logger(
    log_file,
    level=logging.INFO,
    max_bytes=5 * 1024 * 1024,
    backup_count=2,
):
    logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # avoid duplicate logs

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler = handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
