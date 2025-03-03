import pika
import json
import asyncio
from app.utils.logger import DefaultLogger
from app.core.scrapper import scrape_articles_base, scrape_articles_content
from app.utils.date_formatter import format_date_str, secure_date_range
from app.models import SourceScrapeRequest
from app.utils.services import get_sources, post_articles_bulk, notify_orchestrator
from app.rabbitmq.connection import RabbitMQConnection

logger = DefaultLogger("ExtractionService").get_logger()

async def process_extraction_task(task_payload: dict):
    logger.info("Processing extraction task from RabbitMQ")

    # Expected
    source_name = task_payload.get("name")
    date_base_str = task_payload.get("date_base")
    date_cutoff_str = task_payload.get("date_cutoff")
    correlation_id = task_payload.get("correlation_id")

    if not source_name or not date_base_str or not date_cutoff_str or not correlation_id:
        logger.error("Missing required fields in task payload")
        return
    
    date_base, date_cutoff = secure_date_range(date_base_str, date_cutoff_str)
    
    try:
        sources_list = await get_sources()
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        return
    
    source_dict = next(
        (src for src in sources_list if src.get("name", "").lower() == source_name.lower()),
        None
    )
    if not source_dict:
        logger.error(f"Source '{source_name}' not found in Storage Service")
        return
    
    articles = scrape_articles_base(source_dict, date_base, date_cutoff)
    logger.debug(f"Scraped {len(articles)} base articles")

    articles_content = scrape_articles_content(articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    try:
        await post_articles_bulk(articles_content)
    except Exception as e:
        logger.error(f"Error posting articles: {e}")
        return
    
    # Notify orchestrator that extraction is complete
    try:
        await notify_orchestrator(correlation_id, {
            "status": "extraction_complete",
            "articles_count": len(articles_content)
        })
    except Exception as e:
        logger.error(f"Error notifying orchestrator: {e}")
    
    logger.info("Extraction task completed successfully")

def callback(ch, method, properties, body):
    logger.info("Received message from RabbitMQ")
    try:
        task_payload = json.loads(body)
    except Exception as e:
        logger.error(f"Error decoding message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)
        return
    try:
        asyncio.run(process_extraction_task(task_payload))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Message acknowledged")
    except Exception as e:
        logger.error(f"Error processing extraction task: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def start_consumer():
    try:
        logger.info("Starting consumer: getting channel from RabbitMQConnection")
        channel = RabbitMQConnection.get_channel()
        logger.info("Channel obtained successfully")
        channel.queue_declare(queue='extraction-tasks', durable=True)
        logger.info("Queue 'extraction-tasks' declared")
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='extraction-tasks', on_message_callback=callback)
        logger.info("Basic consume set for 'extraction-tasks'; entering consuming loop")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Error in RabbitMQ consumer: {e}")