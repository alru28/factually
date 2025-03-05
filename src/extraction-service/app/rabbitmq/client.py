import asyncio
import json
from fastapi.encoders import jsonable_encoder
import logging
from aio_pika import connect_robust, Message, ExchangeType
from app.utils.logger import DefaultLogger
import os

RABBITMQ_CONNECTION_STRING = os.getenv(
    "RABBITMQ_CONNECTION_STRING", "amqp://guest:guest@rabbitmq:5672/%2F"
)

logger = DefaultLogger("ExtractionService").get_logger()

class RabbitMQClient:
    def __init__(self, rabbitmq_url: str, exchange_name: str, queues: dict = None):
        """
        queues: dict mapping queue name to routing key(s)
                e.g. {"orchestrator_queue": "task.completion", "extraction_queue": "extraction.task"}
        """
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.queues_def = queues or {}  # initial queue definitions
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queues = {}  # will hold declared queue objects

    async def connect(self):
        """Establish a connection, channel and declare exchange & initial queues."""
        self.connection = await connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            ExchangeType.TOPIC,
            durable=True
        )
        # Declare each initial queue and bind it
        for queue_name, routing_keys in self.queues_def.items():
            await self.declare_queue(queue_name, routing_keys)
        logger.info("Connected and declared exchange and queues.")

    async def declare_queue(self, queue_name: str, routing_keys):
        """Declare a queue and bind it with the provided routing key(s).
           routing_keys can be a single string or a list of strings.
        """
        queue = await self.channel.declare_queue(queue_name, durable=True)
        if isinstance(routing_keys, str):
            routing_keys = [routing_keys]
        for rk in routing_keys:
            await queue.bind(self.exchange, routing_key=rk)
            logger.info(f"Bound queue {queue_name} to exchange {self.exchange_name} with routing key '{rk}'.")
        self.queues[queue_name] = queue

    async def publish(self, message_body: dict, routing_key: str):
        """Publish a JSON-encoded message to a specified routing key."""
        body = json.dumps(jsonable_encoder(message_body)).encode("utf-8")
        message = Message(
            body = body,
            content_type='application/json',
            delivery_mode=2
        )
        await self.exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published message to {routing_key}: {message_body}")

    async def consume(self, queue_name: str, callback):
        """Start consuming messages from a specific declared queue."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} is not declared.")
        await queue.consume(callback)
        logger.info(f"Started consuming messages from queue: {queue_name}")

    async def close(self):
        """Cleanly close the connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection.")

async def get_rabbitmq_client() -> RabbitMQClient:
    """
    Returns a singleton instance of RabbitMQClient.
    Initializes it (and connects) if not already done.
    """
    global _instance
    if _instance is None:
        queues = {
            "tasks_transformation": "transformation",
            "tasks_extraction": "extraction",
            "tasks_completion": "completion"
        }
        _instance = RabbitMQClient(
            rabbitmq_url=RABBITMQ_CONNECTION_STRING,
            exchange_name="orchestration_exchange",
            queues=queues
        )
        await _instance.connect()
        logger.info("Initialized RabbitMQ singleton client.")
    return _instance

async def close_rabbitmq_client():
    """
    Closes the RabbitMQ client and resets the singleton instance.
    """
    global _instance
    if _instance:
        await _instance.close()
        _instance = None
        logger.info("Closed RabbitMQ singleton client.")

_instance: RabbitMQClient = None

# Example usage in a microservice (e.g., orchestrator.py)
if __name__ == "__main__":
    import json

    async def handle_task_completion(message):
        body = json.loads(message.body.decode('utf-8'))
        print("Received task completion:", body)
        await message.ack()

    async def main():
        # Define multiple queues with their routing keys.
        queues = {
            "orchestrator_queue": "task.completion",
            "extraction_queue": "extraction.task",
            "transformation_queue": "transformation.task"
        }
        client = RabbitMQClient(
            rabbitmq_url="amqp://guest:guest@localhost/",
            exchange_name="service_exchange",
            queues=queues
        )
        await client.connect()
        # Start consuming from orchestrator_queue
        await client.consume("orchestrator_queue", handle_task_completion)
        # Example: publish an extraction task
        await client.publish({"task": "extraction", "pipeline_id": "123"}, routing_key="extraction.task")
        # Keep the service running indefinitely
        await asyncio.Future()

    asyncio.run(main())
