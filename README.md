# Furlenco Product Scraper

A Python script to scrape product information from Furlenco's website. The script fetches both list and detailed views of products and combines them into a comprehensive dataset.

## Features

- Fetches product listings and detailed information
- Combines data from both views into a single record
- Saves data in JSON format with daily files
- Automatic periodic updates (every 5 minutes)
- Robust error handling and logging
- Rate limiting to avoid server overload

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python script.py
```

The script will:

- Start scraping products every 5 minutes
- Save data to `data/products_YYYYMMDD.json`
- Log progress and any errors to console

## Data Structure

Products are saved with the following structure:

```json
{
    "id": 123,
    "title": "Product Name",
    "permalink": "product-url-slug",
    "available": true,
    "availableUnits": 10,
    "lineOfProduct": "RENT",
    "pricing": {
        "discount": {...},
        "discountPercentage": {...},
        "monthlyRental": {...},
        "strikePrice": {...}
    },
    "description": "Product description",
    "specifications": {...},
    "features": [...],
    "dimensions": {...},
    "additionalInfo": {...}
}
```

## Configuration

The script includes configurable parameters:

- Scraping interval (default: 5 minutes)
- Request delay (default: 0.1 seconds between requests)
- City and pincode settings in headers

## Error Handling

- Logs errors for invalid responses
- Continues operation on individual product failures
- Maintains data consistency with validation
- Graceful shutdown on keyboard interrupt

## Data Storage

- Data is stored in the `data` directory
- Files are named by date: `products_YYYYMMDD.json`
- Each product is saved immediately after fetching
- Previous data is preserved and updated

## Requirements

- Python 3.6+
- requests
- pydantic

See `requirements.txt` for full list of dependencies.
