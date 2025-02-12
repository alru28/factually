from datetime import date, timedelta
from typing import List
from bs4 import BeautifulSoup
import time
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from app.utils.url_helpers import safe_url_format
from app.utils.logger import DefaultLogger
from app.core.article_processing import process_articles_base
from app.core.driver import scroll_down, init_driver
from app.models import ArticleBase
from app.config import sources

def obtain_urls(source: str, date_base: date, date_cutoff: date):
    urls = set()
    current_date = date_base
    while current_date > date_cutoff:
        url = safe_url_format(source['url'], year=current_date.year, month=f"{current_date.month:02d}", day=f"{current_date.day:02d}")
        urls.add(url)
        current_date -= timedelta(days=1)
    return urls

def collect_articles(source: str, driver, url: str, date_base: date, date_cutoff: date):
    DefaultLogger().get_logger().debug(f"Processing: {url}")

    try:
        driver.get(url)
        scroll_down(driver)
    except WebDriverException as e:
        DefaultLogger().get_logger().error(f"Error loading {url}: No articles were collected.", exc_info=True)
        return None

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('div', class_=sources[source]['article_selector'])

    articles_processed, older_than_cutoff = process_articles_base(articles, sources[source], date_base, date_cutoff)

    return articles_processed, older_than_cutoff

def scrape_articles_base(source: str, date_base: date, date_cutoff: date) -> List[ArticleBase]:
    driver = init_driver()

    article_list = []

    urls = obtain_urls(sources[source], date_base, date_cutoff)
    DefaultLogger().get_logger().info(f"Collecting article links from {source}")
    for url in urls:
        # IF THERE'S PAGE IN TEMPLATE -> PAGINATION
        if '{page}' in sources[source]['url']:
            page_number = 1
            while True:
                url_params = {
                    "page": page_number
                }

                # INSERT PAGE NUMBER IN URL
                formatted_url = safe_url_format(url, **url_params)

                articles_processed, older_than_cutoff = collect_articles(source, driver, formatted_url, date_base, date_cutoff)
                article_list.extend(articles_processed)

                if not articles_processed or older_than_cutoff:
                    break

                page_number += 1

        # IF THERE'S BUTTON SELECTOR -> LOAD MORE PATTERN
        elif sources[source]['button_selector']:
            while True:
                # This list holds the articles so that no duplicates appear when including the newly loaded ones
                load_more_article_list = []
                articles_processed, older_than_cutoff = collect_articles(source, driver, url, date_base, date_cutoff)
                load_more_article_list.extend(articles_processed)

                if not articles_processed or older_than_cutoff:
                    break
                else:
                    try:
                        load_more_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, sources[source]['button_selector']))
                        )
                        driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
                        load_more_btn.click()
                        DefaultLogger().get_logger().debug("Loading more articles with button")
                        time.sleep(2)
                    except (TimeoutException, ElementClickInterceptedException):
                        DefaultLogger().get_logger().warning("No more articles could be loaded with button")
                        break
            article_list.extend(load_more_article_list)

        # IF NO PAGINATION OR LOAD MORE -> COLLECT ARTICLES          
        else:
            articles_processed, older_than_cutoff = collect_articles(source, driver, url, date_base, date_cutoff)
            article_list.extend(articles_processed)

    driver.quit()
    return article_list