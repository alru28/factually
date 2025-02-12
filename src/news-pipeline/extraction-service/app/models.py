from typing import List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field, HttpUrl, field_validator

class ArticleBase(BaseModel):
    Title: str = Field(default="DefaultTitle")
    Date: str = Field(default_factory=lambda: date.today().isoformat())
    Link: HttpUrl

    @field_validator("Date", mode='before')
    def validate_fecha(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value

class Reference(BaseModel):
    text: str
    link: str

class Article(ArticleBase):
    paragraphs: Optional[List[str]] = Field(default_factory=list)
    references: Optional[List[Reference]] = Field(default_factory=list)