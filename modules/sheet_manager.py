
import gspread
import pandas as pd
from typing import List, Optional
from google.oauth2.service_account import Credentials


class GoogleSheetsError(Exception):
    """Raised when Google Sheets operations fail."""
    pass


class GoogleSheetsManager:
    """A class to manage Google Sheets operations for product data."""
    
    def __init__(self, credentials_path: str, sheet_id: str, worksheet_name: str = "Sheet1"):
        """
        Initialize the GoogleSheetsManager.
        
        Args:
            credentials_path: Path to the Google service account JSON credentials file
            sheet_id: Google Sheets document ID (from the URL)
            worksheet_name: Name of the worksheet/tab to work with
            
        Raises:
            GoogleSheetsError: If authentication or sheet access fails
        """
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        
        try:
            # Define the scope for Google Sheets API
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate using service account credentials
            creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet and worksheet
            self.spreadsheet = self.client.open_by_key(sheet_id)
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to initialize Google Sheets connection: {e}")
    
    def get_product_codes(self, start_row: int = 2) -> List[str]:
        """
        Extract product codes from column A of the Google Sheet.
        
        Args:
            start_row: Row number to start reading from (default: 2 to skip header)
            
        Returns:
            List of product codes (non-empty strings only)
            
        Raises:
            GoogleSheetsError: If reading from the sheet fails
        """
        try:
            # Get all values from column A starting from the specified row
            col_a_values = self.worksheet.col_values(1)  # Column A is index 1
            
            # Extract values from start_row onwards (convert to 0-based index)
            if len(col_a_values) >= start_row:
                product_codes = col_a_values[start_row - 1:]
                # Filter out empty strings and whitespace-only entries
                product_codes = [code.strip() for code in product_codes if code.strip()]
                return product_codes
            else:
                return []
                
        except Exception as e:
            raise GoogleSheetsError(f"Failed to read product codes from sheet: {e}")
    
    def update_sheet_with_dataframe(self, df: pd.DataFrame, start_row: int = 2, start_col: str = "B"):
        """
        Update the Google Sheet with data from a pandas DataFrame.
        
        Args:
            df: Pandas DataFrame containing the product data
            start_row: Row number to start writing data (default: 2 to preserve header)
            start_col: Column letter to start writing data (default: "B")
            
        Raises:
            GoogleSheetsError: If updating the sheet fails
        """
        try:
            # Convert start_col letter to column number (B=2, C=3, etc.)
            start_col_num = ord(start_col.upper()) - ord('A') + 1
            
            # Prepare the data to write
            # First, write the headers
            headers = df.columns.tolist()
            header_range = f"{start_col}{start_row - 1}"
            
            # Calculate the end column for headers
            end_col_num = start_col_num + len(headers) - 1
            end_col_letter = chr(ord('A') + end_col_num - 1)
            header_end_range = f"{end_col_letter}{start_row - 1}"
            
            # Write headers
            self.worksheet.update(f"{header_range}:{header_end_range}", [headers])
            
            # Convert DataFrame to list of lists for batch update
            data_values = df.values.tolist()
            
            if data_values:
                # Calculate the range for data
                end_row = start_row + len(data_values) - 1
                data_range = f"{start_col}{start_row}:{end_col_letter}{end_row}"
                
                # Write data
                self.worksheet.update(data_range, data_values)
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to update sheet with DataFrame: {e}")
    
    def clear_data_columns(self, start_col: str = "B", end_col: str = "H", start_row: int = 1):
        """
        Clear existing data in specified columns to prepare for new data.
        
        Args:
            start_col: Starting column to clear (default: "B")
            end_col: Ending column to clear (default: "H") 
            start_row: Starting row to clear from (default: 1)
            
        Raises:
            GoogleSheetsError: If clearing the sheet fails
        """
        try:
            # Get the last row with data to determine clear range
            last_row = len(self.worksheet.col_values(1))  # Use column A to determine last row
            
            if last_row >= start_row:
                clear_range = f"{start_col}{start_row}:{end_col}{last_row}"
                self.worksheet.batch_clear([clear_range])
                
        except Exception as e:
            raise GoogleSheetsError(f"Failed to clear data columns: {e}")
    
    def get_sheet_info(self) -> dict:
        """
        Get basic information about the current sheet.
        
        Returns:
            Dictionary with sheet information
        """
        try:
            return {
                'title': self.spreadsheet.title,
                'worksheet_name': self.worksheet.title,
                'row_count': self.worksheet.row_count,
                'col_count': self.worksheet.col_count,
                'url': self.spreadsheet.url
            }
        except Exception as e:
            raise GoogleSheetsError(f"Failed to get sheet info: {e}")
    
    def add_headers_if_missing(self, headers: List[str], row: int = 1, start_col: str = "B"):
        """
        Add headers to the sheet if they don't exist.
        
        Args:
            headers: List of header names
            row: Row number for headers (default: 1)
            start_col: Starting column for headers (default: "B")
        """
        try:
            start_col_num = ord(start_col.upper()) - ord('A') + 1
            end_col_num = start_col_num + len(headers) - 1
            end_col_letter = chr(ord('A') + end_col_num - 1)
            
            header_range = f"{start_col}{row}:{end_col_letter}{row}"
            self.worksheet.update(header_range, [headers])
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to add headers: {e}")