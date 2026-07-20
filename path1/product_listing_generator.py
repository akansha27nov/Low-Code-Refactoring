"""
AI-Automated Product Listing Generation
Author: Akansha Verma
Description: Use ChatGPT's vision capabilities to generate compelling product listings automatically
"""

import json
from openai import OpenAI
from .image_utils import encode_image_to_base64
from .prompt_builder import create_product_listing_prompt
from .data_loader import load_product_dataset
from .config import validate_config, OPENAI_API_KEY, DATA_DIR, IMAGES_DIR, OUTPUT_FILE, MAX_IMAGES_TO_SAVE
from .api_client import OpenAIListingClient
from .config import MODEL_NAME, MAX_TOKENS, TEMPERATURE
from .logging_config import setup_logging

# ======================================================
# Step 1: Initialize client with open ai key
# =======================================================

validate_config()
client = OpenAI(api_key=OPENAI_API_KEY)

listing_client = OpenAIListingClient(
    api_key=OPENAI_API_KEY,
    model=MODEL_NAME,
    max_tokens=MAX_TOKENS,
    temperature=TEMPERATURE
)

logger = setup_logging()
# ======================================================
# Step 2: Preparing the Dataset
# =======================================================

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Load dataset from HuggingFace
print("Loading product dataset...")
products_df = load_product_dataset()
logger.info(f"Loaded {len(products_df)} products")
print(f"Dataset columns: {products_df.columns.to_list()}")
# save images locally
print("Saving images locally...")
for i, row in products_df.iterrows():
    try:
        row["image"].save(f"{IMAGES_DIR}/{i}.jpg")
    except Exception as e:
        print(f"[main] Warning: could not save image {i}: {e}")
    if i >= MAX_IMAGES_TO_SAVE:
        break
 
print(f"\n✓ Dataset prepared!")
print(f"Total products: {len(products_df)}")

# ======================================================
# Step 3: Encoding Images for API
# =======================================================

# Example usage
sample_path = products_df.iloc[0]["image"]
encoded_image = encode_image_to_base64(sample_path)
print(f"Encoded image length: {len(encoded_image)} characters")
print(f"Encoded prefix: {encoded_image[:40]}...")

# ======================================================
# Step 4: Creating the Product Listing Prompt
# =======================================================
 
print("\n" + "="*50)
print("PROMPT TEMPLATE")
print("="*50)

prod_from_dataset = products_df.iloc[0]
test_prompt = create_product_listing_prompt(prod_from_dataset)
print(test_prompt[:500] + "...")  # Show first 500 characters

# ======================================================
# Step 5: Calling the ChatGPT API with Vision
# =======================================================

print("\n" + "="*50)
print("TEST")
print("="*50)
encoded_img = encode_image_to_base64(products_df.iloc[0]["image"])
listing_prompt = create_product_listing_prompt(products_df.iloc[0])
product_json = listing_client.generate_listing(encoded_img, listing_prompt)

if product_json:
    print("✓ Successfully generated listing:")
    print(json.dumps(product_json, indent=2))

# =======================================================
# Step 6: Processing Multiple Products
# =======================================================
all_results = []

print(f"Starting batch processing for {len(products_df)} products...")
for index, row in products_df.iterrows():
    print(f"[{index + 1}/{len(products_df)}] Processing: {row.get('productDisplayName', 'Unknown')}")
        
        # encode image
    try:
        encoded_img = encode_image_to_base64(row["image"])
    except ValueError as e:
        logger.warning(f"Skipping row {index}: image encoding failed - {e}")
        continue

        
    # create prompt
    try:
        prompt = create_product_listing_prompt(row)   
        result = listing_client.generate_listing(encoded_img, prompt)
    except Exception as e:
        print(
            f"[main] {type(e).__name__} at row {index} during API call: {e}\n"
            f"Context: product='{row.get('productDisplayName', 'unknown')}'\n"
            f"Suggestion: check API key, rate limits, or network connection."
        )
        continue
        
    # save result
    if result:
        result["product_id"] = row.get("id") # Keep track of which product this is
        all_results.append(result)
        
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(all_results, f, indent=4)
        except OSError as e:
            print(
                f"[main] {type(e).__name__} while saving results at row {index}: {e}\n"
                f"Context: writing to {OUTPUT_FILE}\n"
                f"Suggestion: check disk space, write permissions, or that the parent directory exists."
            )
        

print(f"\n✓ Batch complete! Results saved to {OUTPUT_FILE}")

print("\n" + "="*50)
print("BATCH PROCESSING SUMMARY")
print("="*50)
print(f"Total products processed: {len(all_results)}")
