"""Configuration and environment validation."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "product_images"
OUTPUT_FILE = DATA_DIR / "processed_listings.json"

DATASET_NAME = "ashraq/fashion-product-images-small"
DATASET_SPLIT = "train[:50]"
MAX_IMAGES_TO_SAVE = 100
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 500
TEMPERATURE = 0.6


def validate_config():
    """
    Check required environment/config before running anything else.

    Raises:
        RuntimeError: if OPENAI_API_KEY is missing.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "[validate_config] RuntimeError: OPENAI_API_KEY is not set.\n"
            "Context: checked environment variables and .env file.\n"
            "Suggestion: create a .env file with OPENAI_API_KEY=sk-... "
            "or export it in your shell before running."
        )