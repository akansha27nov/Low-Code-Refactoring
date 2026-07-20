"""Dataset loading for the product listing generator."""

import pandas as pd
from datasets import load_dataset


def load_product_dataset(dataset_name: str = "ashraq/fashion-product-images-small",
                          split: str = "train[:10]") -> pd.DataFrame:
    """
    Load the product dataset from HuggingFace and return it as a DataFrame.

    Parameters:
        dataset_name: HuggingFace dataset identifier
        split: dataset split/slice to load

    Returns:
        DataFrame with an 'image' column (PIL Image objects) plus product metadata.

    Raises:
        RuntimeError: if the dataset can't be loaded. This is intentionally NOT
        caught and silently replaced with a fallback — a fallback with a different
        schema would break every downstream function that expects an 'image' column.
    """
    try:
        dataset = load_dataset(dataset_name, split=split)
    except Exception as e:
        raise RuntimeError(
            f"[load_product_dataset] {type(e).__name__}: {e}\n"
            f"Context: failed to load '{dataset_name}' (split='{split}') from HuggingFace.\n"
            f"Suggestion: check internet connection, HF Hub status, or that the "
            f"'datasets' package is installed and up to date."
        ) from e

    products_df = pd.DataFrame(dataset)

    if "image" not in products_df.columns:
        raise RuntimeError(
            f"[load_product_dataset] RuntimeError: loaded dataset has no 'image' column.\n"
            f"Context: columns found were {products_df.columns.to_list()}.\n"
            f"Suggestion: confirm the dataset name/split is correct."
        )

    return products_df