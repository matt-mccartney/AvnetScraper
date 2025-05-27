import requests
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple


class ProductNotFoundError(Exception):
    """Raised when a product is not found in the API response."""
    pass


class APIRequestError(Exception):
    """Raised when API request fails."""
    pass


class ProductInfoFetcher:
    """
    A class to fetch product information from Avnet API for multiple product numbers.
    
    auth_token: str Bearer Token from Avnet
    """
    
    PRODUCT_INFO_ENDPOINT = "https://apigw.avnet.com/external/fspmicro-application-amer/api/application/product/search"
    
    def __init__(self, auth_token: str):
        """Initialize the ProductInfoFetcher with session and headers."""
        self.session = requests.Session()
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Authorization": auth_token,
            "ocp-apim-subscription-key": "67d1a6d942fc4352a64df2a2cfeb3615",
        }
    
    def _build_request_payload(self, product_number: str) -> Dict:
        """Build the request payload for a given product number."""
        return {
            "filter": "Sboat eq 'G'",
            "top": 5,
            "skip": 0,
            "isIncludeCount": True,
            "isProductImageInclude": False,
            "isSkipFacets": True,
            "orderby": "search.score() desc, ERPMFRPartNumber asc",
            "search": product_number
        }
    
    def fetch_single_product(self, product_number: str, save_to_file: Optional[str] = None) -> Dict:
        """
        Fetch product information for a single product number.
        
        Args:
            product_number: The product number to search for
            save_to_file: Optional filename to save the raw JSON response
            
        Returns:
            Dictionary containing the API response
            
        Raises:
            APIRequestError: If the API request fails
        """
        try:
            payload = self._build_request_payload(product_number)
            response = self.session.post(
                self.PRODUCT_INFO_ENDPOINT,
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("IsSuccessFull"):
                raise APIRequestError(f"API returned unsuccessful response for {product_number}")
            
            if save_to_file:
                with open(save_to_file, "w") as f:
                    json.dump(data, f, indent=4)
            
            return data
            
        except requests.RequestException as e:
            raise APIRequestError(f"Network error fetching data for {product_number}: {e}")
    
    def extract_product_info(self, api_response: Dict) -> Tuple[str, str, str, str]:
        """
        Extract item number, manufacturer, stock, and country of origin from API response.
        
        Args:
            api_response: The API response dictionary
            
        Returns:
            Tuple of (item_number, manufacturer, stock, country_of_origin)
            
        Raises:
            ProductNotFoundError: If no product is found in the response
        """
        data = api_response.get("Data", {})
        product_count = data.get("Count", 0)
        
        if product_count >= 1:
            first_result = data["Products"][0]
            item_num = first_result.get("ItemNumber", "")
            manufacturer = first_result.get("ManufacturerName", "")
            stock = first_result.get("Stock", "")
            country_of_origin = first_result.get("sap_originating_countryoforigin", "")
            return (item_num, manufacturer, stock, country_of_origin)
        
        raise ProductNotFoundError("No products found in API response")
    
    def fetch_multiple_products(self, product_numbers: List[str], save_responses: bool = False) -> Dict[str, Dict]:
        """
        Fetch product information for multiple product numbers.
        
        Args:
            product_numbers: List of product numbers to search for
            save_responses: Whether to save individual API responses to files
            
        Returns:
            Dictionary with structure:
            {
                product_number: {
                    'success': bool,
                    'data': (item_number, manufacturer, stock, country_of_origin) if success else None,
                    'error': error_message if not success else None
                }
            }
        """
        results = {}
        
        for product_number in product_numbers:
            try:
                filename = f"{product_number}_data.json" if save_responses else None
                api_response = self.fetch_single_product(product_number, filename)
                product_info = self.extract_product_info(api_response)
                
                results[product_number] = {
                    'success': True,
                    'data': product_info,
                    'error': None
                }
                
            except (APIRequestError, ProductNotFoundError) as e:
                results[product_number] = {
                    'success': False,
                    'data': None,
                    'error': str(e)
                }
        
        return results
    
    def get_results_dataframe(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Convert results to a pandas DataFrame.
        
        Args:
            results: Output from fetch_multiple_products
            
        Returns:
            DataFrame with columns: product_number, success, item_number, manufacturer, stock, country_of_origin, error
        """
        data_rows = []
        
        for product_number, result in results.items():
            if result['success']:
                item_num, manufacturer, stock, country_of_origin = result['data']
                data_rows.append({
                    'product_number': product_number,
                    'success': True,
                    'item_number': item_num,
                    'manufacturer': manufacturer,
                    'stock': stock,
                    'country_of_origin': country_of_origin,
                    'error': None
                })
            else:
                data_rows.append({
                    'product_number': product_number,
                    'success': False,
                    'item_number': None,
                    'manufacturer': None,
                    'stock': None,
                    'country_of_origin': None,
                    'error': result['error']
                })
        
        return pd.DataFrame(data_rows)
    
    def print_results_summary(self, results: Dict[str, Dict]):
        """Print a summary of all results using the DataFrame."""
        df = self.get_results_dataframe(results)
        
        print("\n" + "="*50)
        print("SUMMARY OF RESULTS")
        print("="*50)
        
        success_count = df['success'].sum()
        total_count = len(df)
        print(f"Successfully processed: {success_count}/{total_count}")
        print("-" * 50)
        print(df.to_string(index=False))
        print()
    
    def get_successful_results(self, results: Dict[str, Dict]) -> Dict[str, Tuple[str, str, str, str]]:
        """
        Extract only successful results from fetch_multiple_products output.
        
        Args:
            results: Output from fetch_multiple_products
            
        Returns:
            Dictionary mapping product numbers to (item_number, manufacturer, stock, country_of_origin) tuples
        """
        return {
            product_number: result['data'] 
            for product_number, result in results.items() 
            if result['success']
        }


# Example usage:
if __name__ == "__main__":
    AUTH_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSIsImtpZCI6IkNOdjBPSTNSd3FsSEZFVm5hb01Bc2hDSDJYRSJ9.eyJhdWQiOiJhcGk6Ly84ZTUxYjk4ZS01N2Q0LTQ4YWUtOGQ5OC01ZjQwNzlkNTE3MzAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC84ODIwMjc5Yi1jMGJlLTRiZGUtODNlZC1mZTZiNmY5NzI0ZDUvIiwiaWF0IjoxNzQ4MzE2MTMwLCJuYmYiOjE3NDgzMTYxMzAsImV4cCI6MTc0ODMyMDAzMCwiYWlvIjoiazJSZ1lPajZkOFNQei9LR1VZUE5oRDN6MTUrZUJRQT0iLCJhcHBpZCI6IjgxZjAwMDIxLTJkZGEtNGQ2Yy1iZTM1LTUxYTE4MTY5YzQyOSIsImFwcGlkYWNyIjoiMSIsImlkcCI6Imh0dHBzOi8vc3RzLndpbmRvd3MubmV0Lzg4MjAyNzliLWMwYmUtNGJkZS04M2VkLWZlNmI2Zjk3MjRkNS8iLCJvaWQiOiJiY2EwNjNlOC1lZjY1LTQyYjgtYmY2Ni1mNTk0YTM1MDFlMTciLCJyaCI6IjEuQVZzQW15Y2dpTDdBM2t1RDdmNXJiNWNrMVk2NVVZN1VWNjVJalpoZlFIblZGekJiQUFCYkFBLiIsInJvbGVzIjpbIkFwaW0uZnNwbWljcm8tYW1lci5SZWFkV3JpdGUuQWxsIl0sInN1YiI6ImJjYTA2M2U4LWVmNjUtNDJiOC1iZjY2LWY1OTRhMzUwMWUxNyIsInRpZCI6Ijg4MjAyNzliLWMwYmUtNGJkZS04M2VkLWZlNmI2Zjk3MjRkNSIsInV0aSI6IlBYcGJiQUNtWDBLcEFkcW9yTzFBQUEiLCJ2ZXIiOiIxLjAiLCJ4bXNfZnRkIjoiOWtmX1VqN09PZ2k1ZE9uMTFUZThQQVMwRU0tNnZ4SllQazlGLWc2b29wWUJkWE5sWVhOMExXUnpiWE0ifQ.YWLB4DEWV48R4RbHQnjHMaWmEwNbtSWLrhRG0YnJolVB_rZepfdqorrqEWlD0j5UJdK4spJRWeEbQX76b-_Up88t39YIgEgxwz-HqmrqFYH7525CpggpOv0Zd07rQPRvfFwmk1qVXb9llRph7IiyuXGypdwjHuqquWzcAsVawZF23RagngAGop0TztgmfH71qRHYhq8w7wJ2inN6R_IBgrRoc43KS6H_P7gkY1Zvg2fYMwZrZXooiIZZ-9EEB0enC-rFPuOjJfFneMuOs9TxR-NlvQn7jCYwGuE88zzg3CHvTxJA-ub3mHooBUqFjq4IhwWqi1HWOtLQ1O3qSVnVbA"

    # Example product numbers array
    product_numbers = ["UMK105B7104KV-FR", "GRM155R71H104KE14D", "CC0402KRX7R9BB104", "GRT21BR61E226ME13L", "CC0805MKX5R8BB226"]
    
    # Create fetcher instance
    fetcher = ProductInfoFetcher(AUTH_TOKEN)
    results = fetcher.fetch_multiple_products(product_numbers)
    fetcher.print_results_summary(results)