from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.models import (
    SummarizeRequest, SummarizeResponse, ArticleSummary,
    SentimentRequest, SentimentResponse, ArticleSentiment,
    ClassificationRequest, ClassificationResponse, ArticleClassification
) 
from app.rabbitmq.operations import publish_message
from app.utils.logger import DefaultLogger
from app.nlp.processor import NLPProcessor


logger = DefaultLogger("TransformationService").get_logger()

nlp_processor = NLPProcessor()

router = APIRouter()

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_article(request: SummarizeRequest):
    logger.info(f"Received summarize request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        try:
            summary = await nlp_processor.summarize(article_id)
            results.append(ArticleSummary(article_id=article_id, summary=summary))
        except Exception as e:
            logger.error(f"Error summarizing article {article_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error summarizing article {article_id}: {str(e)}")
    logger.info(f"Summarized {len(results)} articles")
    return SummarizeResponse(results=results)

@router.post("/sentiment", response_model=SentimentResponse)
async def sentiment_analysis(request: SentimentRequest):
    logger.info(f"Received sentiment analysis request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        try:
            sentiment_result = await nlp_processor.analyze_sentiment(str(article_id))
            results.append(ArticleSentiment(
                article_id=article_id, 
                sentiment=sentiment_result["label"], 
                score=sentiment_result["score"]
            ))
        except Exception as e:
            logger.error(f"Error analyzing sentiment for article {article_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error analyzing sentiment for article {article_id}: {str(e)}")
    logger.info(f"Analyzed sentiment for {len(results)} articles")
    return SentimentResponse(results=results)

@router.post("/classify", response_model=ClassificationResponse)
async def classify_article(request: ClassificationRequest):
    logger.info(f"Received classification request for article_ids: {request.article_ids}")
    results = []
    for article_id in request.article_ids:
        try:
            classification_result = await nlp_processor.classify(str(article_id))
            confidence = classification_result["scores"].get(classification_result["label"], None)
            results.append(ArticleClassification(
                article_id=article_id, 
                category=classification_result["label"], 
                confidence=confidence
            ))
        except Exception as e:
            logger.error(f"Error classifying article {article_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error classifying article {article_id}: {str(e)}")
    logger.info(f"Classificated {len(results)} articles")
    return ClassificationResponse(results=results)
