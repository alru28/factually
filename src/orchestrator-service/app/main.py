from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from app.utils.logger import DefaultLogger
from app.rabbitmq.connection import RabbitMQConnection
from app.rabbitmq.setup import declare_exchange_queues
from app.api.routes import router as workflow_router
import uvicorn

logger = DefaultLogger("OrchestrationService").get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        channel = RabbitMQConnection.get_channel()
        logger.info("RabbitMQ Channel obtained")
        declare_exchange_queues(channel)
        logger.info("Queues and Exchange declared")
    except Exception as e:
        logger.error(f"Error during RabbitMQ initialization: {e}")

    # App running
    yield

    # RabbitMQ shutdown
    try:
        RabbitMQConnection.close_channel()
        logger.info("RabbitMQ Channel closed")
        RabbitMQConnection.close_connection()
        logger.info("RabbitMQ Connection closed")
    except Exception as e:
        logger.error(f"Error during RabbitMQ shutdown: {e}")

app = FastAPI(lifespan=lifespan, title="OrchestrationService", openapi_url="/openapi.json")

app.include_router(workflow_router, prefix="/api")

if __name__ == "__main__":
    logger.info("Starting Orchestration Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)