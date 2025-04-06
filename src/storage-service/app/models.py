from typing import List, Optional
from datetime import date
from uuid import uuid4
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArticleBase(BaseModel):
    """
    Base model for an article.

    Attributes:
        _id (str): Unique identifier for the article.
        Title (str): Title of the article.
        Date (str): Date of publication of the article.
        Link (HttpUrl): URL link to the article.
        Source (HttpUrl): URL of the article source.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    Title: str = Field(default="DefaultTitle", description="Title of the article")
    Date: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Date of publication of the article",
    )
    Link: HttpUrl
    Source: HttpUrl

    @field_validator("Date", mode="before")
    def validate_dates(cls, value):
        """
        Validates and converts the Date field to ISO format if it is a date instance.

        Args:
            value (str or date): The date value to validate.

        Returns:
            str: ISO formatted date string.
        """
        if isinstance(value, date):
            return value.isoformat()
        return value


class Reference(BaseModel):
    """
    Model representing a reference within an article.

    Attributes:
        Text (str): The reference text.
        Link (HttpUrl): The URL link of the reference.
    """

    Text: str
    Link: HttpUrl


class Article(ArticleBase):
    """
    Extended article model with additional content fields.

    Attributes:
        Paragraphs (Optional[List[str]]): List of text paragraphs forming the article.
        References (Optional[List[Reference]]): List of references included within the article.
    """

    Paragraphs: Optional[List[str]] = Field(
        default_factory=list, description="List of chunks of text forming the article"
    )
    References: Optional[List[Reference]] = Field(
        default_factory=list,
        description="List of references included within the text of the article",
    )
    Summary: Optional[str] = Field(None, description="A brief summary of the article")
    Sentiment: Optional[str] = Field(None, description="Sentiment analysis of the article (e.g., positive, neutral, negative)")
    Classification: Optional[List[str]] = Field(
        default_factory=list, description="Classification tags or categories for the article"
    )


class Source(BaseModel):
    """
    Model representing a source for scraping articles.

    Attributes:
        _id (Optional[str]): Unique identifier for the source.
        name (str): Unique name of the source.
        base_url (HttpUrl): Base URL of the source.
        url (str): URL pattern for scraping articles.
        article_selector (Optional[str]): CSS selector to locate articles.
        date_format (Optional[str]): Expected date format for date extraction.
        button_selector (Optional[str]): CSS selector for navigation button, if any.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Unique name of the source")
    base_url: HttpUrl
    url: str = Field(..., description="URL pattern for scraping")
    article_selector: Optional[str] = Field(
        None, description="CSS selector to locate articles"
    )
    date_format: Optional[str] = Field(None, description="Expected date format")
    button_selector: Optional[str] = Field(
        None, description="CSS selector for navigation button, if any"
    )

class SearchResult(BaseModel):
    Title: str
    Date: str
    Content: str
    Source: str

def article_helper(article) -> Article:
    """
    Converts a MongoDB article document into an Article model object.

    The function extracts the '_id' field from the document, converts it to a string and assigns it as 'id',
    then parses the resulting dictionary into an Article instance.

    Args:
        article (dict): The MongoDB document representing an article.

    Returns:
        Article: The parsed Article model instance.
    """
    article["id"] = article["_id"]
    del article["_id"]
    return Article.model_validate(article)


def source_helper(source) -> Source:
    """
    Converts a MongoDB source document into a Source model object.

    The function extracts the '_id' field from the document, converts it to a string and assigns it as 'id',
    then parses the resulting dictionary into a Source instance.

    Args:
        source (dict): The MongoDB document representing a source.

    Returns:
        Source: The parsed Source model instance.
    """
    source["id"] = source["_id"]
    del source["_id"]
    return Source.model_validate(source)

def article_to_weaviate_object(article: Article) -> dict:
    content_parts = [article.Title]
    if article.Summary:
        content_parts.append(f"Summary: {article.Summary}")
    if article.Sentiment:
        content_parts.append(f"Sentiment: {article.Sentiment}")
    if article.Classification:
        content_parts.append(f"Classification: {', '.join(article.Classification)}")
    if article.Paragraphs:
        content_parts.extend(article.Paragraphs)
    
    content = "\n".join(content_parts)
    
    return {
        "Title": article.Title,
        "Content": content,
        "Date": article.Date,
        "Source": str(article.Source),
    }