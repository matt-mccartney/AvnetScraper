from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import random

class AvnetTokenScraper:
    """
    A class to scrape the Avnet Americas website with stealth techniques,
    detect challenge pages (like CAPTCHAs), and extract the 'randomVal' input value.
    """

    def __init__(self, headless=False):
        """
        Initializes the Chrome WebDriver with stealth options.

        Args:
            headless (bool): If True, runs the browser in headless mode (without a UI).
        """
        self.driver = None
        self.wait = None
        self.actions = None
        self.viewport_width = random.randint(1200, 1400)
        self.viewport_height = random.randint(700, 900)
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        """
        Configures Chrome options for maximum stealth and initializes the WebDriver.
        """
        chrome_options = Options()
        
        # Disable automation indicators
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Window size and position to mimic real user
        chrome_options.add_argument(f"--window-size={self.viewport_width},{self.viewport_height}")
        chrome_options.add_argument("--start-maximized")
        
        # Disable various automation detection methods
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins-discovery")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-default-apps")
        
        # Set language and locale
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en-US,en;q=0.9',
            'profile.default_content_setting_values.notifications': 2
        })

        if self.headless:
            chrome_options.add_argument("--headless=new") # Use new headless mode

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.actions = ActionChains(self.driver)
            self._apply_stealth_scripts()
            print("WebDriver initialized with stealth options.")
        except WebDriverException as e:
            print(f"Error initializing WebDriver: {e}")
            print("Ensure ChromeDriver is installed and its path is correctly configured or in system PATH.")
            self.driver = None # Ensure driver is None if initialization fails

    def _apply_stealth_scripts(self):
        """
        Executes JavaScript to modify browser properties for stealth.
        """
        if not self.driver:
            return

        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override the plugins property to mimic real browser
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override languages property
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

    def _check_for_challenge(self, wait_time=5):
        """
        Checks if the current page is a challenge page (e.g., CAPTCHA, Cloudflare).
        Returns True if a challenge is detected, False otherwise.
        """
        if not self.driver:
            print("Driver not initialized, cannot check for challenge.")
            return False

        print("Checking for potential challenge pages...")
        try:
            # Wait for any of the common challenge page indicators to appear
            self.wait.until(
                EC.any_of(
                    EC.title_contains("Just a moment..."), # Common Cloudflare title
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Access Denied"),
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Verify you are human"),
                    EC.presence_of_element_located((By.ID, "cf-browser-verification")), # Cloudflare specific ID
                    EC.presence_of_element_located((By.CLASS_NAME, "g-recaptcha")), # Google reCAPTCHA class
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Please wait...')]")), # Generic waiting text
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Checking your browser')]")) # Another generic check
                )
            )
            
            # Also check the current URL for common challenge patterns
            current_url = self.driver.current_url
            if "cdn-cgi" in current_url or "challenge" in current_url or "captcha" in current_url:
                print(f"Challenge detected based on URL: {current_url}")
                return True

            print("Challenge page detected based on content.")
            return True
        except TimeoutException:
            # If none of the conditions are met within the timeout, assume no challenge
            print("No obvious challenge page detected within the timeout.")
            return False
        except Exception as e:
            # Catch any other unexpected errors during the check
            print(f"An unexpected error occurred while checking for challenge: {e}")
            return False

    def _simulate_human_behavior(self):
        """
        Simulates human-like mouse movements and scrolling.
        """
        if not self.driver or not self.actions:
            return

        # Move mouse to random positions to simulate browsing behavior
        for _ in range(3):
            time.sleep(random.uniform(0.5, 1.5))
        
        # Scroll down and up slightly to mimic reading
        self.driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(random.uniform(1, 2))
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.5, 1))

    def scrape_random_value(self, url="https://www.avnet.com/americas/"):
        """
        Navigates to the specified URL, handles potential challenges,
        and extracts the 'randomVal' input value.

        Args:
            url (str): The URL to navigate to.

        Returns:
            str or None: The extracted 'randomVal' or None if not found/error.
        """
        if not self.driver:
            print("Scraper not initialized. Please check WebDriver setup.")
            return None

        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)
            
            # Introduce a random delay to mimic human reading time
            human_delay = random.uniform(2.5, 4.5)
            time.sleep(human_delay)
            
            # Check for challenge page and wait if detected
            if self._check_for_challenge(wait_time=10):
                print("CAPTCHA/Challenge detected. The script will wait for 60 seconds. Manual intervention might be required if running interactively.")
                time.sleep(60) # Wait for a prolonged period
                print("Resuming after wait. Checking if challenge is resolved...")
                # After waiting, check again. If still present, it's likely stuck.
                if self._check_for_challenge(wait_time=5):
                    print("Challenge still present after waiting. Cannot proceed with scraping 'randomVal'.")
                    return None # Exit the function if a challenge is still detected
                else:
                    print("Challenge appears to be resolved. Attempting to proceed.")

            # Wait for the main page body to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("Main page body loaded successfully.")
            except TimeoutException:
                print("Timeout waiting for main page body to load. This might indicate a persistent challenge or extremely slow loading.")
                return None

            self._simulate_human_behavior()
            
            print("Searching for input field with id 'randomVal'...")
            
            try:
                # Use a patient wait for the specific 'randomVal' element
                random_val_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "randomVal"))
                )
                
                random_value = random_val_input.get_attribute("value")
                
                if random_value:
                    print(f"Successfully extracted randomVal: {random_value}")
                    return random_value
                else:
                    placeholder = random_val_input.get_attribute("placeholder")
                    data_value = random_val_input.get_attribute("data-value")
                    
                    if placeholder:
                        print(f"randomVal input found with placeholder: {placeholder}")
                        return placeholder
                    elif data_value:
                        print(f"randomVal input found with data-value: {data_value}")
                        return data_value
                    else:
                        print("randomVal input found but has no value, placeholder, or data-value.")
                        return None
                    
            except TimeoutException:
                print("Input field with id 'randomVal' not found within timeout period.")
                print("This could be due to a challenge page (if not caught earlier), the element not being present, or a different page structure.")
                
                # Enhanced debugging: try to find other inputs that might be related
                try:
                    random_inputs = self.driver.find_elements(By.XPATH, "//input[contains(@id, 'random') or contains(@name, 'random') or contains(@class, 'random')]")
                    if random_inputs:
                        print(f"Found {len(random_inputs)} inputs with 'random' in attributes:")
                        for inp in random_inputs:
                            inp_id = inp.get_attribute("id")
                            inp_name = inp.get_attribute("name")
                            inp_value = inp.get_attribute("value")
                            print(f"  - id='{inp_id}', name='{inp_name}', value='{inp_value}'")
                    
                    all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    print(f"\nFound {len(all_inputs)} total input fields on the page (showing first 15):")
                    for i, inp in enumerate(all_inputs[:15]):
                        inp_id = inp.get_attribute("id")
                        inp_name = inp.get_attribute("name")
                        inp_class = inp.get_attribute("class")
                        inp_type = inp.get_attribute("type")
                        inp_value = inp.get_attribute("value")
                        print(f"Input {i+1}: id='{inp_id}', name='{inp_name}', type='{inp_type}', class='{inp_class}', value='{inp_value[:50] if inp_value else None}'")
                        
                except Exception as debug_error:
                    print(f"Error during debugging element search: {debug_error}")
                
                return None
                
        except WebDriverException as we:
            print(f"A WebDriver error occurred during scraping: {str(we)}")
            print("This often indicates issues with the browser driver or environment setup.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during scraping: {str(e)}")
            return None
            
    def close(self):
        """
        Closes the WebDriver instance.
        """
        if self.driver:
            time.sleep(random.uniform(1, 2)) # Small delay before closing
            self.driver.quit()
            print("Browser closed.")

if __name__ == "__main__":
    # Example usage of the AvnetScraper class
    scraper = None
    try:
        # Set headless=True to run without opening a browser window
        scraper = AvnetTokenScraper(headless=False) 
        result = scraper.scrape_random_value()
        
        if result:
            print(f"\nFinal extracted randomVal: {result}")
        else:
            print("\nNo value was extracted, possibly due to a challenge, element not found, or another error.")
    except Exception as main_error:
        print(f"An error occurred in the main execution block: {main_error}")
    finally:
        if scraper:
            scraper.close()

