import json
import asyncio
from app.utils.logger import DefaultLogger
from app.main import get_rabbitmq_client

logger = DefaultLogger("OrchestrationService").get_logger()

async def publish_message(message: dict, routing_key: str):
    try:
        client = await get_rabbitmq_client()
        await client.publish(message, routing_key)
    except Exception as e:
        logger.error(f"Failed to publish message to routing key '{routing_key}': {e}")

async def handle_message(message):
    payload = json.loads(message.body.decode('utf-8'))
    logger.info("Processing message from RabbitMQ")
    logger.info(f"Task payload: {payload}")
    await message.ack()