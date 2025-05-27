from modules.sheet_manager import GoogleSheetsManager, GoogleSheetsError
from modules.product_info_fetcher import ProductInfoFetcher
from modules.token_fetch import AvnetTokenScraper
import json
import time


if __name__ == "__main__":
    AUTH_TOKEN = None

    with open("config.json", "r") as f:
        data = json.load(f)
        assert data["sheets"] and data["sheets"]["credentials_path"] and data["sheets"]["sheet_id"] and data["sheets"]["worksheet_name"]

    if data.get("token") == None or time.time() - data.get("token").get("sourced_at") > (30*60):
        scraper = AvnetTokenScraper(headless=False) 
        AUTH_TOKEN = scraper.scrape_random_value()
        data["token"] = {
            "value": AUTH_TOKEN,
            "sourced_at": time.time()
        }
        if AUTH_TOKEN != None:
            with open("config.json", "w+") as f:
                f.write(json.dumps(data, indent=4))
    else:
        AUTH_TOKEN = data["token"]["value"]
 
    try:
        # You'll need to provide your own credentials file and sheet ID
        sheets_manager = GoogleSheetsManager(
            credentials_path=data["sheets"]["credentials_path"],
            sheet_id=data["sheets"]["sheet_id"],
            worksheet_name=data["sheets"]["worksheet_name"]
        )
        
        # Get sheet information
        info = sheets_manager.get_sheet_info()
        print(f"Connected to sheet: {info['title']}")
        print(f"Worksheet: {info['worksheet_name']}")
        
        # Extract product codes from column A
        product_codes = sheets_manager.get_product_codes(start_row=2)
        print(f"Found {len(product_codes)} product codes:")
        for code in product_codes[:5]:  # Show first 5
            print(f"  - {code}")
        
        fetcher = ProductInfoFetcher(AUTH_TOKEN)
        results = fetcher.fetch_multiple_products(product_codes)
        df = fetcher.get_results_dataframe(results)
        
        # Clear existing data (optional)
        sheets_manager.clear_data_columns(start_col="B", end_col="H")
        
        # Update sheet with DataFrame
        sheets_manager.update_sheet_with_dataframe(df, start_row=2, start_col="B")
        
        print("Sheet updated successfully!")
        
    except GoogleSheetsError as e:
        print(f"Google Sheets error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")