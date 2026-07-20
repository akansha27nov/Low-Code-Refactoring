"""Prompt construction for product listing generation."""


def create_product_listing_prompt(product) -> str:
    """
    Create a prompt for generating a product listing via vision API.

    Parameters:
        product: A dict-like object (e.g. pandas Series) with optional keys
            'productDisplayName', 'masterCategory', 'gender', 'baseColour',
            'season', 'usage'. Missing keys fall back to defaults.

    Returns:
        Formatted prompt string ready to send to the API.

    Raises:
        ValueError: if product is None or doesn't support .get()
    """
    if product is None:
        raise ValueError(
            "[create_product_listing_prompt] ValueError: product is None.\n"
            "Context: expected a dict-like row with product fields.\n"
            "Suggestion: check that the dataframe row was passed correctly."
        )

    if not hasattr(product, "get"):
        raise ValueError(
            f"[create_product_listing_prompt] ValueError: product of type "
            f"{type(product).__name__} has no .get() method.\n"
            f"Context: expected a dict or pandas Series.\n"
            f"Suggestion: pass a single row (e.g. df.iloc[i]), not a DataFrame or list."
        )

    prompt = f"""
    Role: You are an expert e-commerce copywriter. 
    Task: Analyze the product image and create a compelling product listing.
    Product Information:
    - Name: {product.get('productDisplayName', 'Unknown Product')}
    - Category: {product.get('masterCategory', 'N/A')}
    - Gender: {product.get('gender', 'Unisex')}
    - Color: {product.get("baseColour", "N/A")}
    - Season: {product.get("season", "N/A")}
    - Usage: {product.get("usage", "N/A")}
    
    Please create a professional product listing that includes:
 
    1. **Product Title** (catchy, SEO-friendly, 60 characters max)
    2. **Product Description** (detailed,engaging, 150-200 words)
        - Highlight key features and benefits
        - Use persuasive language
        - Include relevant details visible in the image
    3. **Key Features** (bullet points, 5-7 items)
    4. **SEO Keywords** (comma-separated, 10-15 relevant keywords)
    
    Format your response as JSON with the following structure:
    {{
        "title": "Product title here",
        "description": "Full description here",
        "features": ["Feature 1", "Feature 2", ...],
        "keywords": "keyword1, keyword2, ..."
    }}
    
    Be specific about what you see in the image. Mention colors, materials, design elements, and any distinctive features."""

    return prompt