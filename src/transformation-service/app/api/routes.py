from fastapi import APIRouter, BackgroundTasks, HTTPException
from uuid import UUID
from app.models import (
    SummarizeRequest, SummarizeResponse, ArticleSummary,
    SentimentRequest, SentimentResponse, ArticleSentiment,
    ClassificationRequest, ClassificationResponse, ArticleClassification
) 
from app.rabbitmq.operations import publish_message
from app.utils.logger import DefaultLogger


logger = DefaultLogger("TransformationService").get_logger()

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_article(request: SummarizeRequest):
    logger.info(f"Received summarize request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        # SUMMARY LOGIC

        # Dummy logic
        summary = f"Summary for article {article_id}"
        results.append(ArticleSummary(article_id=article_id, summary=summary))
    logger.info(f"Summarized {len(results)} articles")
    return SummarizeResponse(results=results)

@router.post("/sentiment", response_model=SentimentResponse)
async def sentiment_analysis(request: SentimentRequest):
    logger.info(f"Received sentiment analysis request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        # SA LOGIC

        # Dummy logic
        sentiment = "positive"
        score = 0.85
        results.append(ArticleSentiment(article_id=article_id, sentiment=sentiment, score=score))
    logger.info(f"Analyzed sentiment for {len(results)} articles")
    return SentimentResponse(results=results)

@router.post("/classify", response_model=ClassificationResponse)
async def classify_article(request: ClassificationRequest):
    logger.info(f"Received classification request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        # CLASSIFICATION LOGIC

        # Dummy logic
        category = "News"
        confidence = 0.95
        results.append(ArticleClassification(article_id=article_id, category=category, confidence=confidence))
    logger.info(f"Classificated {len(results)} articles")
    return ClassificationResponse(results=results)
