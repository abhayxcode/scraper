import requests
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for data structure
class ImageWithAspectRatio(BaseModel):
    aspectRatio: float
    url: str

class PricingValue(BaseModel):
    displayValue: str
    value: float

class PricingDiscount(BaseModel):
    discount: PricingValue
    discountPercentage: PricingValue
    monthlyRental: PricingValue
    strikePrice: PricingValue

# Base product model with common fields
class BaseProduct(BaseModel):
    id: int
    title: str
    permalink: Optional[str]
    available: bool
    availableUnits: int
    lineOfProduct: str
    pricing: PricingDiscount
    vertical: str
    thumbnail: ImageWithAspectRatio
    heroes: List[ImageWithAspectRatio]

    class Config:
        extra = "ignore"

# Model for products from list view
class ListProduct(BaseProduct):
    pass

# Combined product model
class Product(BaseModel):
    # Fields from list view
    id: int
    title: str
    permalink: Optional[str]
    available: bool
    availableUnits: int
    lineOfProduct: str
    pricing: PricingDiscount
    vertical: str
    thumbnail: ImageWithAspectRatio
    heroes: List[ImageWithAspectRatio]
    
    # Additional fields from detailed view
    description: Optional[str]
    specifications: Optional[Dict]
    variantConfiguration: Optional[List[Dict]]
    collection: Optional[List[Dict]]
    features: Optional[List[Dict]]
    dimensions: Optional[Dict]
    additionalInfo: Optional[Dict]
    
    class Config:
        extra = "ignore"

class ProductResponse(BaseModel):
    total_count: int
    products: List[Union[ListProduct, Product]]

def get_headers():
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'moriarty': 'web-1.0',
        'origin': 'https://www.furlenco.com',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-city-id': '6',
        'x-pincode': '201010'
    }

def get_all_products() -> Optional[ProductResponse]:
    url = "https://ciago.furlenco.com/api/v1/catalogue/products"
    params = {
        "collectionType": "CATEGORY_RENT",
        "city": "noida",
        "collection": "bedroom-furniture-on-rent",
        "collectionName": "bedroom-furniture-on-rent"
    }
    
    try:
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or 'data' not in data or 'products' not in data['data']:
            logger.error("Invalid response format")
            return None
        
        try:
            # Convert each product to a dictionary if it isn't already
            products_data = []
            for product in data['data']['products']:
                if isinstance(product, dict):
                    products_data.append(product)
                else:
                    products_data.append(product.dict() if hasattr(product, 'dict') else dict(product))
            
            return ProductResponse(
                products=products_data,
                total_count=len(products_data)
            )
        except Exception as e:
            logger.error(f"Error converting products data: {str(e)}")
            logger.error(f"Raw products data: {json.dumps(data['data']['products'][:2], indent=2)}")  # Log first 2 products for debugging
            return None
    
    except requests.RequestException as e:
        logger.error(f"Error fetching products: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Error details: {str(e)}")
        return None

def get_product_details(list_product: ListProduct) -> Optional[Product]:
    """Get detailed product information and merge it with list view data"""
    url = f"https://ciago.furlenco.com/api/v1/catalogue/products/{list_product.permalink}"
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        
        data = response.json()
        if not data or 'data' not in data:
            logger.error(f"Invalid product details response format for {list_product.permalink}")
            return None

        # Create a dictionary with list view data
        merged_data = list_product.dict()
        
        # Update with detailed view data
        detailed_data = data['data']
        
        # Keep the pricing from list view as it's more complete
        pricing_data = merged_data.get('pricing', {})
        
        # Update all fields except pricing
        for key, value in detailed_data.items():
            if value is not None and key != 'pricing':  # Skip pricing from detailed view
                merged_data[key] = value
        
        # Ensure pricing is preserved
        merged_data['pricing'] = pricing_data
        
        try:
            # Create complete product with merged data
            return Product(**merged_data)
        except Exception as e:
            logger.error(f"Validation error for {list_product.permalink}: {str(e)}")
            logger.error(f"Merged data: {json.dumps(merged_data, indent=2)}")
            return None
        
    except requests.RequestException as e:
        logger.error(f"Error fetching product details for {list_product.permalink}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in product details for {list_product.permalink}: {str(e)}")
        return None

def save_product_to_file(product: Product):
    """Save a single product to the daily JSON file
    
    Args:
        product: Product to save
    """
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Use today's date for the filename
    today = datetime.now().strftime("%Y%m%d")
    filename = output_dir / f"products_{today}.json"
    
    # Load existing data if file exists
    data = {
        "totalProducts": 0,
        "products": []
    }
    
    if filename.exists():
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not read existing file {filename}, starting fresh")
    
    # Add new product to existing data and update count
    data["products"].append(product.dict())
    data["totalProducts"] = len(data["products"])
    
    # Save the updated data
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved product {product.id} (Total products: {data['totalProducts']})")

def main():
    interval = 300  # 5 minutes
    logger.info("Starting product scraper...")
    
    while True:
        try:
            # Get all products
            products_response = get_all_products()
            if products_response and products_response.products:
                logger.info(f"Found {len(products_response.products)} products in list view")
                
                # Get and save detailed information for each product
                products_processed = 0
                for list_product in products_response.products:
                    try:
                        # Ensure list_product is a dictionary before conversion
                        list_product_dict = list_product if isinstance(list_product, dict) else list_product.dict()
                        list_product_obj = ListProduct(**list_product_dict)
                        product_details = get_product_details(list_product_obj)
                        if product_details:
                            # Save each product immediately after fetching its details
                            save_product_to_file(product_details)
                            products_processed += 1
                        time.sleep(0.1)  # Small delay between requests to avoid rate limiting
                    except Exception as e:
                        # Use safe attribute access for error logging
                        product_id = (
                            list_product.get('id', 'unknown') if isinstance(list_product, dict)
                            else getattr(list_product, 'id', 'unknown')
                        )
                        logger.error(f"Error processing product {product_id}: {str(e)}")
                        continue
                
                logger.info(f"Finished processing {products_processed} products")
            else:
                logger.warning("No products were retrieved")
                
            logger.info(f"Waiting {interval} seconds before next scrape...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            logger.info("Scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            time.sleep(interval)

if __name__ == "__main__":
    main()
