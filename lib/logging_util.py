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
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": log_file,
                "maxBytes": max_bytes,
                "backupCount": backup_count,
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": level,
            "handlers": ["file", "console"],
        },
    }

    logging.config.dictConfig(config)
