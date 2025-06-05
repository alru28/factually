from pydantic import BaseModel, validator
from typing import List, Optional
from uuid import UUID

class ArticleRequest(BaseModel):
    article_ids: List[UUID]

    @validator("article_ids", pre=True)
    def ensure_list(cls, v):
        if not isinstance(v, list):
            return [v]
        return v

class SummarizeRequest(ArticleRequest):
    pass

class ArticleSummary(BaseModel):
    article_id: UUID
    summary: str

class SummarizeResponse(BaseModel):
    results: List[ArticleSummary]

class SentimentRequest(ArticleRequest):
    pass

class ArticleSentiment(BaseModel):
    article_id: UUID
    sentiment: str
    score: Optional[float] = None

class SentimentResponse(BaseModel):
    results: List[ArticleSentiment]

class ClassificationRequest(ArticleRequest):
    pass

class ArticleClassification(BaseModel):
    article_id: UUID
    category: str
    confidence: Optional[float] = None

class ClassificationResponse(BaseModel):
    results: List[ArticleClassification]
