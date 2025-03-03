from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger
from app.rabbitmq.connection import RabbitMQConnection
from app.rabbitmq.setup import declare_exchange_queues
import uvicorn


logger = DefaultLogger("OrchestrationService").get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # RabbitMQ Init
    channel = RabbitMQConnection.get_channel()
    logger.info("RabbitMQ Channel obtained")
    declare_exchange_queues(channel)
    logger.info("Queues and Exchange declared")
    
    # App running
    yield

    # RabbitMQ shutdown
    RabbitMQConnection.close_channel()
    logger.info("RabbitMQ Channel closed")
    RabbitMQConnection.close_connection()
    logger.info("RabbitMQ Connection closed")

app = FastAPI(lifespan=lifespan, title="OrchestrationService", openapi_url="/openapi.json")


if __name__ == "__main__":
    logger.info("Starting Orchestration Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
