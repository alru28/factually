import json
import asyncio
from app.utils.logger import DefaultLogger
from app.main import get_rabbitmq_client

logger = DefaultLogger().get_logger()

async def publish_message(message: dict, routing_key: str):
    try:
        client = await get_rabbitmq_client()
        await client.publish(message, routing_key)
    except Exception as e:
        logger.error(f"Failed to publish message to routing key '{routing_key}': {e}")

async def handle_message(message):
    payload = json.loads(message.body.decode('utf-8'))

    correlation_id = payload.get("correlation_id")
    status = payload.get("status")
    article_ids = payload.get("article_ids")
    if not article_ids:
        logger.error("No article IDs found in the payload")
        return
    
    if status == "extraction_complete":
        logger.info(f"Completed extraction task with correlation_id: {correlation_id}")
        message_payload = {
            "correlation_id": correlation_id,
            "status": "transformation",
            "article_ids": article_ids,
            "article_count": len(article_ids),
        }
        await publish_message(message=message_payload, routing_key="transformation")
        logger.info(f"Published transformation task with correlation_id: {correlation_id}")
        
    elif status == "transformation_complete":
        logger.info(f"Completed transformation task with correlation_id: {correlation_id}")
    else:
        logger.error(f"Unknown status '{status}' in the payload")
        return

    await message.ack()