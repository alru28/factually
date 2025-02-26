import pika
import os

RABBITMQ_CONNECTION_STRING = os.getenv(
    "RABBITMQ_CONNECTION_STRING", "http://rabbitmq:5672"
)

def get_connection():
    parameters = pika.URLParameters(RABBITMQ_CONNECTION_STRING)
    return pika.BlockingConnection(parameters)

def get_channel():
    connection = get_connection()
    channel = connection.channel()
    return channel
