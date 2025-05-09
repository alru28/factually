import json
import asyncio
from app.utils.logger import DefaultLogger
from app.main import get_rabbitmq_client
from app.utils.date_formatter import secure_date_range
from app.utils.services import get_sources, post_articles_bulk
from app.core.scraper import scrape_articles_base, scrape_articles_content

logger = DefaultLogger().get_logger()

async def publish_message(message: dict, routing_key: str):
    try:
        client = await get_rabbitmq_client()
        await client.publish(message, routing_key)
    except Exception as e:
        logger.error(f"Failed to publish message to routing key '{routing_key}': {e}")

async def handle_message(message):
    message_dict = json.loads(message.body.decode('utf-8'))

    payload = message_dict.get("payload")
    sources = payload.get("sources")
    date_base_str = payload.get("date_base")
    date_cutoff_str = payload.get("date_cutoff")
    correlation_id = message_dict.get("correlation_id")

    logger.info(f"Processing extraction request from RabbitMQ | CorrelationID: {correlation_id}")
    
    required = {
        "sources": sources,
        "date_base": date_base_str,
        "date_cutoff": date_cutoff_str,
        "correlation_id": correlation_id,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        logger.error(f"Missing required fields in task payload: {missing}. Full payload: {message_dict}")
        return
    
    date_base, date_cutoff = secure_date_range(date_base_str, date_cutoff_str)
    
    try:
        sources_list = await get_sources()
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        return

    payload_sources = set(s.lower() for s in sources)
    matching_sources = [src for src in sources_list if src.get("name", "").lower() in payload_sources]
    
    if not matching_sources or len(matching_sources) != len(payload_sources):
        logger.error(f"Some of the sources specified not found in Storage Service: {sources}")
        return

    articles = []
    for src in matching_sources:
        articles_from_src = scrape_articles_base(src, date_base, date_cutoff)
        logger.debug(f"Scraped {len(articles_from_src)} base articles from source {src.get('name')}")
        articles.extend(articles_from_src)
    
    logger.debug(f"Total scraped base articles: {len(articles)}")
    articles_content = scrape_articles_content(articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    try:
        created_articles = await post_articles_bulk(articles_content)
    except Exception as e:
        logger.error(f"Error posting articles: {e}")
        return
    
    article_ids = [article.get("id") for article in created_articles]

    try:
        message_payload = {
        "correlation_id":correlation_id,
        "status":"extraction_complete",
        "article_ids": article_ids,
        "article_count": len(article_ids),
        } 
        await publish_message(message_payload, 'completion')
    except Exception as e:
        logger.error(f"Error notifying orchestrator: {e}")
    
    logger.info("Extraction task completed successfully")

    await message.ack()