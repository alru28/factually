from pydantic import BaseModel, validator
from typing import List, Optional
from uuid import UUID

class ArticleRequest(BaseModel):
    article_ids: List[UUID]

    # Single or list
    @validator("article_ids", pre=True)
    def ensure_list(cls, v):
        if not isinstance(v, list):
            return [v]
        return v

# Summarize
class SummarizeRequest(ArticleRequest):
    pass

class ArticleSummary(BaseModel):
    article_id: UUID
    summary: str

class SummarizeResponse(BaseModel):
    results: List[ArticleSummary]

# SA
class SentimentRequest(ArticleRequest):
    pass

class ArticleSentiment(BaseModel):
    article_id: UUID
    sentiment: str
    score: Optional[float] = None  # Optional numeric sentiment score

class SentimentResponse(BaseModel):
    results: List[ArticleSentiment]

# Classification
class ClassificationRequest(ArticleRequest):
    pass

class ArticleClassification(BaseModel):
    article_id: UUID
    category: str
    confidence: Optional[float] = None  # Confidence score

class ClassificationResponse(BaseModel):
    results: List[ArticleClassification]
