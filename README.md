# Avnet Scraper

This tool was designed to assist in collecting information from the [Avnet](https://www.avnet.com/americas/) website, more specifically the manufacturer and it's country of origin.

This tool utilizes various webscraping techniques including Authorization workarounds, Request-based querying, and managing dynamically rendered content via Selenium.

With this tool, it is possible to scrape nearly all information regarding a product, provided you have a list of product numbers.

There is integration with Google Sheets, allowing users to easily update, view, and share scraped data with necessary people.

## Installation

In order to use this tool, you must install a few libraries that it depends on: Pandas, Requests, Selenium, Gspread, and Google Oauth 2.0.

First, create a virtual environment. Once this is done, open the project directory and install the packages:
```py
pip3 install -r requirements.txt
```

### Google Service Account

In order to use the Google Sheets API integration, you will need a service account. Once your account is [set up](https://cloud.google.com/iam/docs/service-accounts-create), export your credentials from the dashboard as a JSON file, and drop your credentials inside of the project directory

### Setting up your Configuration File

Create a copy of `config.sample.json` and fill in all relevant fields.

#### Sample Config
```json
{
    "sheets": {
        "credentials_path": "credentials.json",
        "sheet_id": "YOUR_GOOGLE_SHEET_ID_HERE",
        "worksheet_name": "Sheet1"
    }
}
```
- `credentials_path`: The filename of your Google Service Account JSON key file (e.g., "credentials.json").
- `sheet_id`: The unique ID of your Google Sheet. You can find this in the sheet's URL (e.g., https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit).
- `worksheet_name`: The exact name of the specific worksheet (tab) within your Google Sheet (e.g., "Sheet1", "Product Data").

Once you do this, you are ready to run the program. Token information will auto-populate.

## Running the Application

To run the application, open the project directory in your terminal and simply run the main file in terminal:
```py
python3 main.py
```

## Project Structure

```
.
├── README.md
├── .gitignore
├── config.json              # Your configured settings
├── config.sample.json       # Template for configuration
├── credentials.json         # Your Google Service Account key (example name)
├── main.py
├── requirements.txt
└── modules
    ├── sheet_manager.py
    ├── token_fetch.py
    └── product_info_fetcher.py
```