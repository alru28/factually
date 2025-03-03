import json
import pika
from fastapi.encoders import jsonable_encoder
from app.rabbitmq.connection import RabbitMQConnection
from app.utils.logger import DefaultLogger

logger = DefaultLogger("OrchestrationService").get_logger()

def publish_message(message: dict, routing_key: str):
    try:
        channel = RabbitMQConnection.get_channel()
        body = json.dumps(jsonable_encoder(message))
        channel.basic_publish(
            exchange="ArticleProcessing",
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        logger.info(f"Message published to routing key '{routing_key}': {body}")
    except Exception as e:
        logger.error(f"Failed to publish message to routing key '{routing_key}': {e}")
