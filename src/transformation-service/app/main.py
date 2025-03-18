from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from app.utils.logger import DefaultLogger
from app.rabbitmq.client import get_rabbitmq_client
from app.rabbitmq.operations import handle_message
from app.api.routes import router as nlp_router
import os
import asyncio
import uvicorn


logger = DefaultLogger("TransformationService").get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client = await get_rabbitmq_client()
        logger.info("RabbitMQ Client connected | Queues and Exchange declared")

        asyncio.create_task(client.consume('tasks_completion', callback=handle_message))
    except Exception as e:
        logger.error(f"Error during RabbitMQ initialization: {e}")

    # App running
    yield

    # RabbitMQ shutdown
    try:
        await client.close()
        logger.info("RabbitMQ Client connection closed")
    except Exception as e:
        logger.error(f"Error during RabbitMQ shutdown: {e}")

app = FastAPI(lifespan=lifespan, title="TransformationService", openapi_url="/openapi.json")

app.include_router(nlp_router, prefix="/api")

if __name__ == "__main__":
    logger.info("Starting Transformation Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)