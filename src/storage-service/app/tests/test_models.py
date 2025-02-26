from uuid import uuid4
from app.models import article_helper, source_helper, Article, Source


def test_article_helper():
    """
    Test that the article_helper function correctly converts a MongoDB article document
    into an Article model.
    """
    dummy_article = {
        "_id": str(uuid4()),
        "Title": "Test Article",
        "Date": "2022-01-01",
        "Link": "http://example.com",
        "Source": "http://source.com",
    }
    article = article_helper(dummy_article.copy())
    assert isinstance(article, Article)
    assert article.Title == "Test Article"
    assert "id" in article.model_dump()


def test_source_helper():
    """
    Test that the source_helper function correctly converts a MongoDB source document
    into a Source model.
    """
    dummy_source = {
        "_id": str(uuid4()),
        "name": "Test Source",
        "base_url": "http://source.com",
        "url": "http://source.com/articles",
        "article_selector": ".article",
        "date_format": "%Y-%m-%d",
        "button_selector": None,
    }
    source = source_helper(dummy_source.copy())
    assert isinstance(source, Source)
    assert source.name == "Test Source"
    assert "id" in source.model_dump()
