from typing import List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field, HttpUrl, field_validator

class ArticleBase(BaseModel):
    Title: str = Field(default="DefaultTitle")
    Date: str = Field(default_factory=lambda: date.today().isoformat())
    Link: HttpUrl
    Source: HttpUrl

    @field_validator("Date", mode='before')
    def validate_fecha(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value

class Reference(BaseModel):
    Text: str
    Link: HttpUrl

class Article(ArticleBase):
    Paragraphs: Optional[List[str]] = Field(default_factory=list)
    References: Optional[List[Reference]] = Field(default_factory=list)