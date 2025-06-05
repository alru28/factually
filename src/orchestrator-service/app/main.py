from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.utils.logger import DefaultLogger
from app.rabbitmq.client import get_rabbitmq_client
from app.rabbitmq.operations import handle_message
from app.api.routes import router as workflow_router
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import os
import asyncio
import uvicorn



logger = DefaultLogger().get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing OrchestratorService")
    try:
        client = await get_rabbitmq_client()
        logger.info("RabbitMQ Client connected | Queues and Exchange declared")

        asyncio.create_task(client.consume('tasks_completion', callback=handle_message))
    except Exception as e:
        logger.error(f"Error during RabbitMQ initialization: {e}")

    yield

    try:
        await client.close()
        logger.info("RabbitMQ Client connection closed")
    except Exception as e:
        logger.error(f"Error during RabbitMQ shutdown: {e}")

app = FastAPI(lifespan=lifespan, title="OrchestratorService", openapi_url="/openapi.json")

FastAPIInstrumentor.instrument_app(app)

app.include_router(workflow_router)

if __name__ == "__main__":
    logger.info("Starting Orchestration Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)