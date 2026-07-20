"""Configuration and environment validation for the meal planner.

Replaces google.colab.userdata.get() (Colab-only) with standard env vars,
so this runs anywhere — local, CI, or Colab with a .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "meal-planner-mvp")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

INGREDIENTS_PER_RECIPE = int(os.getenv("INGREDIENTS_PER_RECIPE", "5"))
EXCLUDED_BASICS = ["salt", "pepper", "oil", "garlic", "water"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def validate_config(require_email: bool = False, require_langsmith: bool = False):
    """
    Check required environment variables before running anything else.

    Parameters:
        require_email: also validate EMAIL_SENDER/EMAIL_PASSWORD are set
        require_langsmith: also validate LANGSMITH_API_KEY is set

    Raises:
        RuntimeError: lists every missing required variable at once.
    """
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if require_langsmith and not LANGSMITH_API_KEY:
        missing.append("LANGSMITH_API_KEY")
    if require_email and not EMAIL_SENDER:
        missing.append("EMAIL_SENDER")
    if require_email and not EMAIL_PASSWORD:
        missing.append("EMAIL_PASSWORD")

    if missing:
        raise RuntimeError(
            f"[validate_config] RuntimeError: missing required environment variable(s): "
            f"{', '.join(missing)}\n"
            f"Context: checked process environment and .env file.\n"
            f"Suggestion: create a .env file in the project root with these keys set, "
            f"or export them in your shell before running."
        )