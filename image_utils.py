"""Image encoding utilities for the product listing generator."""

import base64
from io import BytesIO


def encode_image_to_base64(image) -> str:
    """
    Encode a PIL Image to a base64 string (JPEG format).

    Parameters:
        image: PIL Image object

    Returns:
        Base64-encoded string of the image

    Raises:
        ValueError: if image is None or can't be saved as JPEG
    """
    if image is None:
        raise ValueError(
            "[encode_image_to_base64] ValueError: received None instead of an image.\n"
            "Context: check the 'image' column of the product row.\n"
            "Suggestion: verify the dataset loaded correctly before encoding."
        )

    try:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise ValueError(
            f"[encode_image_to_base64] {type(e).__name__}: {e}\n"
            f"Context: failed while saving image to JPEG buffer.\n"
            f"Suggestion: confirm the object is a valid PIL Image (not a file path or bytes)."
        ) from e