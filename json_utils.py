"""JSON extraction utilities for parsing LLM responses.

Consolidates two near-duplicate fence-stripping implementations that
previously lived in MealPlanGenerator.generate() and parse_llm_json().
"""

import json


def strip_markdown_json_fences(content: str) -> str:
    """
    Remove markdown code fences (```json ... ``` or ``` ... ```) from LLM response text.

    Parameters:
        content: raw LLM response text, possibly wrapped in markdown fences

    Returns:
        Content with fences removed, stripped of whitespace.

    Raises:
        ValueError: if content is None.
    """
    if content is None:
        raise ValueError(
            "[strip_markdown_json_fences] ValueError: content is None.\n"
            "Context: expected a string LLM response.\n"
            "Suggestion: check that the LLM call actually returned a response "
            "before passing it here."
        )

    content = content.strip()
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]
    return content.strip()


def parse_json_response(content: str) -> dict:
    """
    Extract and parse JSON from an LLM response, handling markdown fences.

    Parameters:
        content: raw LLM response text

    Returns:
        Parsed JSON as a dict.

    Raises:
        json.JSONDecodeError: if the cleaned content still isn't valid JSON.
            Re-raised with the failing line/column and a preview of the content.
    """
    cleaned = strip_markdown_json_fences(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"[parse_json_response] JSONDecodeError: {e.msg}\n"
            f"Context: failed at line {e.lineno}, column {e.colno} of cleaned LLM response.\n"
            f"Raw content (first 200 chars): {cleaned[:200]}\n"
            f"Suggestion: check the LLM's response_format/prompt, or inspect raw output.",
            e.doc,
            e.pos,
        ) from e