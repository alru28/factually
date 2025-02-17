from datetime import date, timedelta
from typing import List
from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
import time
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from app.utils.url_helpers import safe_url_format
from app.utils.logger import DefaultLogger
from app.core.article_processing import process_articles_base, process_articles_content
from app.core.driver import scroll_down, init_driver
from app.models import ArticleBase, Article

def obtain_urls(source: dict, date_base: date, date_cutoff: date):
    urls = set()
    current_date = date_base
    while current_date > date_cutoff:
        url = safe_url_format(source['url'], year=current_date.year, month=f"{current_date.month:02d}", day=f"{current_date.day:02d}")
        urls.add(url)
        current_date -= timedelta(days=1)
    return urls

def collect_articles(source: dict, driver, url: str, date_base: date, date_cutoff: date):
    DefaultLogger().get_logger().debug(f"Processing: {url}")

    try:
        driver.get(url)
        scroll_down(driver)
    except WebDriverException as e:
        DefaultLogger().get_logger().error(f"Error loading {url}: No articles were collected.", exc_info=True)
        return None

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('div', class_=source['article_selector'])

    articles_processed, older_than_cutoff = process_articles_base(articles, source, date_base, date_cutoff, url)

    return articles_processed, older_than_cutoff

def scrape_articles_base(source: dict, date_base: date, date_cutoff: date) -> List[ArticleBase]:
    driver = init_driver()

    article_list = []

    urls = obtain_urls(source, date_base, date_cutoff)
    DefaultLogger().get_logger().info(f"Collecting article links from {source['name']}")
    for url in urls:
        # IF THERE'S PAGE IN TEMPLATE -> PAGINATION
        if '{page}' in source['url']:
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
        elif source['button_selector']:
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
                            EC.element_to_be_clickable((By.CLASS_NAME, source['button_selector']))
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

def scrape_articles_content_selenium(articles: List[ArticleBase]) -> List[Article]:
    driver = init_driver()

    article_list = []

    DefaultLogger().get_logger().info(f"Scrapping contents from {len(articles)} articles")
    for article in articles:
        try:
            driver.get(str(article.Link))
            scroll_down(driver)
        except WebDriverException as e:
            DefaultLogger().get_logger().error(f"Error loading {str(article.Link)}: No content was extracted.", exc_info=True)
            continue
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        article_content = process_articles_content(article, soup)
        article_list.append(article_content)

    driver.quit()
    return article_list


def scrape_articles_content_requests(articles: List[ArticleBase]) -> List[Article]:
    article_list = []
    DefaultLogger().get_logger().info(f"Scraping contents from {len(articles)} articles")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })

    for article in articles:
        try:
            response = requests.get(str(article.Link), timeout=3, auth=HTTPBasicAuth('user', 'pass'))
            response.raise_for_status()
        except RequestException as e:
            DefaultLogger().get_logger().error(
                f"Error loading {str(article.Link)}: No content was extracted.",
                exc_info=True
            )
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        article_content = process_articles_content(article, soup)
        article_list.append(article_content)

    return article_list

def scrape_articles_content(articles: List[ArticleBase]) -> List[Article]:
    article_list = []
    DefaultLogger().get_logger().info(f"Scraping contents from {len(articles)} articles")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })

    driver = None

    for article in articles:
        use_selenium = False
        
        try:
            response = session.get(str(article.Link), timeout=3, auth=HTTPBasicAuth('user', 'pass'))
            response.raise_for_status()
        except RequestException as e:
            status_code = e.response.status_code if e.response is not None else "N/A"
            DefaultLogger().get_logger().warning(
                f"Requests failed for {article.Link} with status code {status_code}. Falling back to Selenium."
            )
            use_selenium = True
        
        if not use_selenium:
            soup = BeautifulSoup(response.text, 'html.parser')
        else:
            if driver is None:
                driver = init_driver()
            try:
                driver.get(str(article.Link))
                scroll_down(driver)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
            except WebDriverException as e:
                DefaultLogger().get_logger().error(
                    f"Error loading {article.Link} with Selenium: {str(e)}. No content was extracted."
                )
                continue

        article_content = process_articles_content(article, soup)
        article_list.append(article_content)

    if driver is not None:
        driver.quit()
    
    return article_list
