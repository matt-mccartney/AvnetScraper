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

Create a copy of `config.sample.json` and fill in all relevant fields. Once you do this, you are ready to run the program

## Running the Application

To run the application, open the project directory in your terminal and simply run the main file in terminal:
```py
python3 main.py
```

## Project Structure

```
.
|____README.md
|____.gitignore
|____config.sample.json
|____main.py
|____modules
| |____sheet_manager.py
| |____token_fetch.py
| |____product_info_fetcher.py
```