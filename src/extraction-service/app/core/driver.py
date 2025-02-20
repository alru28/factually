import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def init_driver():
    """
    Initializes and returns a headless Selenium WebDriver for web scraping.

    The function configures Chrome options for headless operation,
    disables unnecessary features for performance, and sets the binary location for Chromium.

    Returns:
        WebDriver: An instance of Selenium Chrome WebDriver configured for headless browsing.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium"

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)


def scroll_down(driver, pausa: int = 1):
    """
    Scrolls down the web page until no further scrolling is possible.

    This function repeatedly scrolls down the page and waits for a specified pause interval
    until the page height remains unchanged, indicating the bottom of the page has been reached.

    Args:
        driver: The Selenium WebDriver instance controlling the browser.
        pausa (int, optional): The pause duration in seconds between scroll attempts. Default is 1 second.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pausa)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
