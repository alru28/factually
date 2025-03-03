import pika
import os

RABBITMQ_CONNECTION_STRING = os.getenv(
    "RABBITMQ_CONNECTION_STRING", "amqp://guest:guest@rabbitmq:5672/%2F"
)

class RabbitMQConnection:
    _connection = None
    _channel = None

    @classmethod
    def get_connection(cls):
        """
        Returns a singleton instance of the RabbitMQ connection.
        If the connection is not established or is closed, a new connection is created.
        """
        if cls._connection is None or cls._connection.is_closed:
            parameters = pika.URLParameters(RABBITMQ_CONNECTION_STRING)
            cls._connection = pika.BlockingConnection(parameters)
        return cls._connection

    @classmethod
    def get_channel(cls):
        """
        Returns a singleton instance of the RabbitMQ channel.
        If the channel is not established or is closed, a new channel is created.
        """
        if cls._channel is None or cls._channel.is_closed:
            connection = cls.get_connection()
            cls._channel = connection.channel()
        return cls._channel
    
    @classmethod
    def close_connection(cls):
        """
        Closes the singleton connection
        """
        if cls._connection is not None and not cls._connection.is_closed:
            cls._connection.close()

    @classmethod
    def close_channel(cls):
        """
        Closes the singleton channel
        """
        if cls._channel is not None and not cls._channel.is_closed:
            cls._channel.close()
