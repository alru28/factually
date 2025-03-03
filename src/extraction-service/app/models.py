from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import uuid4
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ScrapeRequest(BaseModel):
    """
    Request model for scraping articles.

    Attributes:
        date_base (str): Base date for scraping (inclusive). Format: DD-MM-YYYY.
        date_cutoff (str): Cutoff date for scraping (exclusive). Format: DD-MM-YYYY.
    """

    date_base: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Base date for scraping (inclusive). Format: DD-MM-YYYY",
    )
    date_cutoff: str = Field(
        default_factory=lambda: (date.today() - timedelta(days=1)).isoformat(),
        description="Cutoff date for scraping (exclusive). Format: DD-MM-YYYY",
    )

    @field_validator("date_base", "date_cutoff", mode="before")
    def validate_dates(cls, value):
        """
        Validates and converts the date fields to ISO format if it is a date instance.

        Args:
            value (str or date): The date value to validate.

        Returns:
            str: ISO formatted date string.
        """
        if isinstance(value, date):
            return value.isoformat()
        return value


class SourceScrapeRequest(ScrapeRequest):
    """
    Extended scraping request model that includes the name of the source.

    Attributes:
        name (str): Name of the source to scrape.
    """

    name: str = Field(..., description="Name of the source to scrape")


class ArticleBase(BaseModel):
    """
    Base model for an article.

    Attributes:
        id (Optional[str]): Unique identifier for the article.
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


class Source(BaseModel):
    """
    Model representing a source for scraping articles.

    Attributes:
        id (Optional[str]): Unique identifier for the source.
        name (str): Unique name of the source.
        base_url (HttpUrl): Base URL of the source.
        url (str): URL pattern for scraping articles.
        article_selector (Optional[str]): CSS selector to locate articles.
        date_format (Optional[str]): Expected date format for date extraction.
        button_selector (Optional[str]): CSS selector for navigation button, if any.
    """

    id: Optional[str] = None
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
