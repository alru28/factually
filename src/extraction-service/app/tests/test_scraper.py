import pytest
from datetime import date
from app.core.scraper import obtain_urls, collect_articles, scrape_articles_base
from app.models import ArticleBase


@pytest.fixture
def source_config():
    return {
        "name": "Test Source",
        "base_url": "http://example.com",
        "url": "http://example.com/{year}/{month}/{day}",
        "article_selector": "article",
        "date_format": "%d-%m-%Y",
        "button_selector": None,
    }


def test_obtain_urls(source_config):
    base_date = date(2022, 1, 5)
    cutoff_date = date(2022, 1, 3)
    urls = obtain_urls(source_config, base_date, cutoff_date)
    expected = {
        "http://example.com/2022/01/05",
        "http://example.com/2022/01/04",
    }
    assert urls == expected

class DummyDriver:
    def __init__(self, html):
        self.page_source = html

    def get(self, url):
        self.page_source = self.page_source

    def execute_script(self, script):
        return 1000

    def quit(self):
        pass


def create_dummy_article_html():
    return """
    <html>
      <body>
        <div class="article">
          <h2>Dummy Article</h2>
          <time>02-01-2022</time>
          <a href="/dummy-article">Link</a>
        </div>
      </body>
    </html>
    """


def test_collect_articles(source_config):
    html = create_dummy_article_html()
    dummy_driver = DummyDriver(html)
    articles_processed, older_than_cutoff = collect_articles(
        source_config,
        dummy_driver,
        "http://example.com/2022/01/02",
        date(2022, 1, 3),
        date(2022, 1, 1),
    )
    assert isinstance(articles_processed, list)
    assert len(articles_processed) == 1
    assert older_than_cutoff is False


def test_scrape_articles_base(monkeypatch, source_config):
    dummy_html = create_dummy_article_html()

    class DummyDriver:
        def __init__(self):
            self.page_source = dummy_html

        def get(self, url):
            self.page_source = dummy_html

        def execute_script(self, script):
            return 1000

        def quit(self):
            pass

    def dummy_init_driver():
        return DummyDriver()

    monkeypatch.setattr("app.core.scraper.init_driver", dummy_init_driver)

    def dummy_collect_articles(source, driver, url, date_base, date_cutoff):
        dummy_article = ArticleBase(
            Title="Dummy Article",
            Date="02-01-2022",
            Link="http://example.com/dummy-article",
            Source=source["base_url"],
        )
        return ([dummy_article], False)

    monkeypatch.setattr("app.core.scraper.collect_articles", dummy_collect_articles)
    articles = scrape_articles_base(source_config, date(2022, 1, 3), date(2022, 1, 1))
    assert isinstance(articles, list)
    assert len(articles) == 2
    assert articles[0].Title == "Dummy Article"
