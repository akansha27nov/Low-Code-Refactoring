"""
AI-Automated Product Listing Generation
Author: Akansha Verma
Description: Use ChatGPT's vision capabilities to generate compelling product listings automatically
"""

import os
import json
import base64
import pandas as pd
from datasets import load_dataset
from pathlib import Path
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

# ======================================================
# Step 1: Initialize client with open ai key
# =======================================================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ======================================================
# Step 2: Preparing the Dataset
# =======================================================

DATA_DIR = Path("data")
# Create images directory
images_dir = DATA_DIR / "product_images"
images_dir.mkdir(parents=True, exist_ok=True)

# Load dataset from HuggingFace
print("Loading product dataset...")
try:
    # Try loading the dataset
    dataset = load_dataset("ashraq/fashion-product-images-small", split="train[:50]")
    print(f"✓ Loaded {len(dataset)} products")
    print(dataset)
    # print(dataset[0]['image'].show()) # show first sample image
    products_df = pd.DataFrame(dataset)
    print(f"Dataset columns: {products_df.columns.to_list()}")
    
    # save image files locally from dataset
    print("Processing and saving images to avoid reading dataset all the time...")
    for i, item in enumerate(dataset):
        img = item["image"]
        img.save(f"{images_dir}/{i}.jpg")
        if i >= 100:
            break
    
except Exception as e:
    print(f"⚠ Could not load HuggingFace dataset: {e}")
    print("Using local images instead...")
    # Alternative: Use local images
    # Create a products.json file with product information
    products_data = [
        {
            "id": 1,
            "name": "Wireless Headphones",
            "price": 79.99,
            "category": "Electronics",
            "image_path": "images/product1.jpg"
        },
        # Add more products...
    ]
    
    products_df = pd.DataFrame(products_data)
 
print(f"\n✓ Dataset prepared!")
print(f"Total products: {len(products_df)}")

# ======================================================
# Step 3: Encoding Images for API
# =======================================================

def encode_image_to_base64(image_path):
    """Encode an image file to base64 string."""
    # following steps are needed to save jpeg file otherwise: 
    # TypeError: expected str, bytes or os.PathLike object, not JpegImageFile
    
    # binary buffer to hold image data 
    buffered = BytesIO()
    # save image to buffer
    image_path.save(buffered, format="JPEG")
    # get the raw bytes from the buffer and encode them
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded 

# Example usage
sample_path = products_df.iloc[0]["image"]
encoded_image = encode_image_to_base64(sample_path)
print(f"Encoded image length: {len(encoded_image)} characters")
print(f"Encoded prefix: {encoded_image[:40]}...")

# ======================================================
# Step 4: Creating the Product Listing Prompt
# =======================================================
def create_product_listing_prompt(product):
    """
    Create a prompt for generating product listings.
    
    Parameters:
    - product_name: Name of the product
    - price: Price of the product
    - category: Product category
    - additional_info: Optional additional information
    
    Returns:
    - Formatted prompt string
    """
    
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
 
print("\n" + "="*50)
print("PROMPT TEMPLATE")
print("="*50)

prod_from_dataset = products_df.iloc[0]
test_prompt = create_product_listing_prompt(prod_from_dataset)
print(test_prompt[:500] + "...")  # Show first 500 characters

# ======================================================
# Step 5: Calling the ChatGPT API with Vision
# =======================================================

def generate_product_listing(encoded_image, prompt_txt):
    """Sends image and prompt to OpenAI and parses JSON."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                        {"type": "text", "text": prompt_txt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    
    except Exception as e:
        print(f"API Call Failed: {e}")
        return None

print("\n" + "="*50)
print("TEST")
print("="*50)
encoded_img = encode_image_to_base64(products_df.iloc[0]["image"])
listing_prompt = create_product_listing_prompt(products_df.iloc[0])
product_json = generate_product_listing(encoded_img, listing_prompt)

if product_json:
    print("✓ Successfully generated listing:")
    print(json.dumps(product_json, indent=2))

# =======================================================
# Step 6: Processing Multiple Products
# =======================================================

output_file = DATA_DIR / "processed_listings.json"
all_results = []

print(f"Starting batch processing for {len(products_df)} products...")
for index, row in products_df.iterrows():
    try:
        print(f"[{index + 1}/{len(products_df)}] Processing: {row.get('productDisplayName', 'Unknown')}")
        
        # encode image
        encoded_img = encode_image_to_base64(row["image"])
        
        # create prompt
        prompt = create_product_listing_prompt(row)
        
        # call open API
        result = generate_product_listing(encoded_img, prompt)
        
        # save result
        if result:
            result["product_id"] = row.get("id") # Keep track of which product this is
            all_results.append(result)
            
            # Save progress incrementally to disk
            with open(output_file, "w") as f:
                json.dump(all_results, f, indent=4)
        
    except Exception as e:
        print(f"⚠ Error processing index {index}: {e}")
        continue

print(f"\n✓ Batch complete! Results saved to {output_file}")

print("\n" + "="*50)
print("BATCH PROCESSING SUMMARY")
print("="*50)
print(f"Total products processed: {len(all_results)}")
