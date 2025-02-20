import copy
import re
from datetime import date
import pytest
from bs4 import BeautifulSoup
from app.core.article_processing import process_articles_base, process_articles_content
from app.models import ArticleBase, Article


# Helper functions to create dummy HTML for testing.
def create_valid_article_html():
    return """
    <div>
      <h2>Test Article Title</h2>
      <time>02-01-2022</time>
      <a href="/article-link">Read More</a>
    </div>
    """


def create_no_link_article_html():
    return """
    <div>
      <h2>Test Article Title</h2>
      <time>02-01-2022</time>
      <!-- Missing link -->
    </div>
    """


def create_no_date_article_html():
    return """
    <div>
      <h2>Test Article Title</h2>
      <a href="/article-link">Read More</a>
    </div>
    """


def create_content_html():
    return """
    <main>
      <p>This is a paragraph that is definitely longer than fifty characters to be considered valid content.</p>
      <p>Short text</p>
      <p>This paragraph contains an <a href="/ref-link">interesting reference</a> for testing purposes.</p>
    </main>
    """


@pytest.fixture
def source_config():
    return {
        "base_url": "http://example.com",
        "url": "http://example.com/{year}/{month}/{day}",
        "date_format": "%d-%m-%Y",
    }


def test_process_articles_base_valid(source_config):
    # Create a BeautifulSoup element from valid HTML.
    soup = BeautifulSoup(create_valid_article_html(), "html.parser")
    # Set date range such that the article date is accepted.
    date_base = date(2022, 1, 3)
    date_cutoff = date(2022, 1, 1)
    articles, older_than_cutoff = process_articles_base(
        [soup], source_config, date_base, date_cutoff, "http://example.com/2022/01/02/"
    )
    # Expect one valid article.
    assert len(articles) == 1
    art = articles[0]
    assert art.Title == "Test Article Title"
    # The flag should be False because the article date is within range.
    assert older_than_cutoff is False


def test_process_articles_base_no_link(source_config):
    # Test that articles with no valid link are skipped.
    soup = BeautifulSoup(create_no_link_article_html(), "html.parser")
    articles, _ = process_articles_base(
        [soup],
        source_config,
        date(2022, 1, 3),
        date(2022, 1, 1),
        "http://example.com/2022/01/02/",
    )
    assert len(articles) == 0


def test_process_articles_base_no_date(source_config):
    # Test fallback behavior when no <time> element is found.
    soup = BeautifulSoup(create_no_date_article_html(), "html.parser")
    articles, _ = process_articles_base(
        [soup],
        source_config,
        date(2022, 1, 3),
        date(2022, 1, 1),
        "http://example.com/2022/01/02/",
    )
    # In our source_config the URL template contains placeholders.
    # The regex in process_articles_base should extract the date "02/01/2022" from the URL.
    assert len(articles) == 1
    art = articles[0]
    # Verify that the date was correctly parsed (format_date_str converts to a date object).
    assert art.Date == "2022-01-02"


def test_process_articles_content():
    # Create a dummy ArticleBase instance.
    article_base = ArticleBase(
        Title="Content Article",
        Date="02-01-2022",
        Link="http://example.com/article",
        Source="http://example.com",
    )
    soup = BeautifulSoup(create_content_html(), "html.parser")
    article = process_articles_content(article_base, soup)
    # Only paragraphs longer than 50 characters should be added.
    assert len(article.Paragraphs) >= 1
    # References should be extracted from <a> tags inside paragraphs.
    assert len(article.References) >= 1
