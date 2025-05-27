from modules.sheet_manager import GoogleSheetsManager, GoogleSheetsError
from modules.product_info_fetcher import ProductInfoFetcher
import json

AUTH_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiJhcGk6Ly84ZTUxYjk4ZS01N2Q0LTQ4YWUtOGQ5OC01ZjQwNzlkNTE3MzAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC84ODIwMjc5Yi1jMGJlLTRiZGUtODNlZC1mZTZiNmY5NzI0ZDUvIiwiaWF0IjoxNzQ4MzE2MTMwLCJuYmYiOjE3NDgzMTYxMzAsImV4cCI6MTc0ODMyMDAzMCwiYWlvIjoiazJSZ1lPajZkOFNQei9LR1VZUE5oRDN6MTUrZUJRQT0iLCJhcHBpZCI6IjgxZjAwMDIxLTJkZGEtNGQ2Yy1iZTM1LTUxYTE4MTY5YzQyOSIsImFwcGlkYWNyIjoiMSIsImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0Lzg4MjAyNzliLWMwYmUtNGJkZS04M2VkLWZlNmI2Zjk3MjRkNS8iLCJvaWQiOiJiY2EwNjNlOC1lZjY1LTQyYjgtYmY2Ni1mNTk0YTM1MDFlMTciLCJyaCI6IjEuQVZzQW15Y2dpTDdBM2t1RDdmNXJiNWNrMVk2NVVZN1VWNjVJalpoZlFIblZGekJiQUFCYkFBLiIsInJvbGVzIjpbIkFwaW0uZnNwbWljcm8tYW1lci5SZWFkV3JpdGUuQWxsIl0sInN1YiI6ImJjYTA2M2U4LWVmNjUtNDJiOC1iZjY2LWY1OTRhMzUwMWUxNyIsInRpZCI6Ijg4MjAyNzliLWMwYmUtNGJkZS04M2VkLWZlNmI2Zjk3MjRkNSIsInV0aSI6IlBYcGJiQUNtWDBLcEFkcW9yTzFBQUEiLCJ2ZXIiOiIxLjAiLCJ4bXNfZnRkIjoiOWtmX1VqN09PZ2k1ZE9uMTFUZThQQVMwRU0tNnZ4SllQazlGLWc2b29wWUJkWE5sWVhOMExXUnpiWE0ifQ.YWLB4DEWV48R4RbHQnjHMaWmEwNbtSWLrhRG0YnJolVB_rZepfdqorrqEWlD0j5UJdK4spJRWeEbQX76b-_Up88t39YIgEgxwz-HqmrqFYH7525CpggpOv0Zd07rQPRvfFwmk1qVXb9llRph7IiyuXGypdwjHuqquWzcAsVawZF23RagngAGop0TztgmfH71qRHYhq8w7wJ2inN6R_IBgrRoc43KS6H_P7gkY1Zvg2fYMwZrZXooiIZZ-9EEB0enC-rFPuOjJfFneMuOs9TxR-NlvQn7jCYwGuE88zzg3CHvTxJA-ub3mHooBUqFjq4IhwWqi1HWOtLQ1O3qSVnVbA"

if __name__ == "__main__":

    with open("config.json", "r") as f:
        data = json.load(f)
        assert data["sheets"] and data["sheets"]["credentials_path"] and data["sheets"]["sheet_id"] and data["sheets"]["worksheet_name"]
 
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