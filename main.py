from modules.sheet_manager import GoogleSheetsManager, GoogleSheetsError
from modules.product_info_fetcher import ProductInfoFetcher
from modules.token_fetch import AvnetTokenScraper
import json
import time
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = "config.json"
TOKEN_EXPIRATION_SECONDS = 30 * 60 # 30 minutes


class ConfigManager:
    def __init__(self, config_path=CONFIG_FILE):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                self._validate_config(data)
                return data
        except FileNotFoundError:
            logging.error(f"Config file not found at {self.config_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file: {self.config_path}")
            raise
        except AssertionError as e:
            logging.error(f"Missing required configuration in {self.config_path}: {e}")
            raise

    def _validate_config(self, data):
        # More robust validation could use Pydantic
        assert data.get("sheets") is not None, "Missing 'sheets' configuration"
        assert data["sheets"].get("credentials_path") is not None, "Missing 'sheets.credentials_path'"
        assert data["sheets"].get("sheet_id") is not None, "Missing 'sheets.sheet_id'"
        assert data["sheets"].get("worksheet_name") is not None, "Missing 'sheets.worksheet_name'"

    def get_sheet_config(self):
        return self.data["sheets"]

    def get_token_data(self):
        return self.data.get("token")

    def set_token_data(self, token_value, sourced_at):
        self.data["token"] = {
            "value": token_value,
            "sourced_at": sourced_at
        }
        self._save_config()

    def _save_config(self):
        try:
            with open(self.config_path, "w") as f: # Use 'w' as 'w+' is less common for simple writes
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            # Optionally re-raise or handle more gracefully


class AuthTokenManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.auth_token = None

    def get_token(self):
        token_data = self.config_manager.get_token_data()
        
        if self._is_token_valid(token_data):
            self.auth_token = token_data["value"]
            logging.info("Using cached authentication token.")
        else:
            logging.info("Authentication token is missing or expired. Scraping new token...")
            self._refresh_token()
            
        if self.auth_token is None:
            raise RuntimeError("Failed to acquire authentication token.")
            
        return self.auth_token

    def _is_token_valid(self, token_data):
        if not token_data:
            return False
        
        value = token_data.get("value")
        sourced_at = token_data.get("sourced_at")
        
        if not value or not sourced_at:
            return False

        if time.time() - sourced_at > TOKEN_EXPIRATION_SECONDS:
            return False
            
        return True

    def _refresh_token(self):
        try:
            scraper = AvnetTokenScraper(headless=True) # Consider making headless configurable
            new_token = scraper.scrape_random_value()
            if new_token:
                self.config_manager.set_token_data(new_token, time.time())
                self.auth_token = new_token
                logging.info("Successfully scraped and saved new authentication token.")
            else:
                logging.warning("Scraping returned an empty token.")
        except Exception as e:
            logging.error(f"Error while scraping new token: {e}")
            self.auth_token = None # Ensure token is cleared on failure


class ProductUpdaterApp:
    def __init__(self, config_manager: ConfigManager, auth_token_manager: AuthTokenManager):
        self.config_manager = config_manager
        self.auth_token_manager = auth_token_manager
        self.sheets_manager = None
        self.product_fetcher = None

    def initialize_sheets_manager(self):
        sheet_config = self.config_manager.get_sheet_config()
        try:
            self.sheets_manager = GoogleSheetsManager(
                credentials_path=sheet_config["credentials_path"],
                sheet_id=sheet_config["sheet_id"],
                worksheet_name=sheet_config["worksheet_name"]
            )
            info = self.sheets_manager.get_sheet_info()
            logging.info(f"Connected to sheet: {info['title']}, Worksheet: {info['worksheet_name']}")
        except GoogleSheetsError as e:
            logging.error(f"Failed to initialize Google Sheets Manager: {e}")
            raise

    def initialize_product_fetcher(self):
        auth_token = self.auth_token_manager.get_token()
        self.product_fetcher = ProductInfoFetcher(auth_token)

    def run(self):
        try:
            self.initialize_sheets_manager()
            self.initialize_product_fetcher()

            logging.info("Extracting product codes from sheet...")
            product_codes = self.sheets_manager.get_product_codes(start_row=2)
            logging.info(f"Found {len(product_codes)} product codes.")
            for code in product_codes[:5]: # Show first 5 for quick check
                logging.debug(f"  - {code}") # Use debug for verbose output

            logging.info("Fetching product information...")
            results = self.product_fetcher.fetch_multiple_products(product_codes)
            df = self.product_fetcher.get_results_dataframe(results)
            logging.info(f"Fetched info for {len(df)} products.")

            logging.info("Clearing existing data columns (B-H)...")
            self.sheets_manager.clear_data_columns(start_col="B", end_col="H")

            logging.info("Updating sheet with new data...")
            self.sheets_manager.update_sheet_with_dataframe(df, start_row=2, start_col="B")
            logging.info("Sheet updated successfully!")

        except GoogleSheetsError as e:
            logging.error(f"Google Sheets operation failed: {e}")
        except RuntimeError as e: # Catching specific errors from token management
            logging.critical(f"Application critical error: {e}")
        except Exception as e:
            logging.critical(f"An unexpected error occurred: {e}", exc_info=True) # exc_info to log traceback

if __name__ == "__main__":
    try:
        config_manager = ConfigManager()
        auth_token_manager = AuthTokenManager(config_manager)
        app = ProductUpdaterApp(config_manager, auth_token_manager)
        app.run()
    except Exception as e:
        logging.critical(f"Application failed to start or run: {e}")