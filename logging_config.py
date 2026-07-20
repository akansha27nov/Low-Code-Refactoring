"""Logging setup for the product listing generator."""

import logging
from pathlib import Path

LOG_FILE = Path("data") / "run.log"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("product_listing_generator")