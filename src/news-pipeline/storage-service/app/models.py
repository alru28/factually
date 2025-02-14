from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, HttpUrl, field_validator

class ArticleBase(BaseModel):
    id: Optional[str] = None
    Title: str = Field(default="DefaultTitle", description="Title of the article")
    Date: str = Field(default_factory=lambda: date.today().isoformat(), description="Date of publication of the article")
    Link: HttpUrl
    Source: HttpUrl

    @field_validator("Date", mode="before")
    def validate_fecha(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value

class Reference(BaseModel):
    Text: str
    Link: HttpUrl

class Article(ArticleBase):
    Paragraphs: Optional[List[str]] = Field(default_factory=list, description="List of chunks of text forming the article")
    References: Optional[List[Reference]] = Field(default_factory=list, description="List of references included within the text of the article")

class Source(BaseModel):
    id: Optional[str] = None
    name: str  = Field(..., description="Unique name of the source")
    base_url: HttpUrl
    url: str = Field(..., description="URL pattern for scraping")
    article_selector: Optional[str] = Field(None, description="CSS selector to locate articles")
    date_format: Optional[str] = Field(None, description="Expected date format")
    button_selector: Optional[str] = Field(None, description="CSS selector for navigation button, if any")
