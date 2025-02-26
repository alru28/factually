from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger
from app.rabbitmq.connection import RabbitMQConnection
from app.rabbitmq.setup import declare_exchange_queues
import uvicorn

app = FastAPI(title="OrchestrationService", openapi_url="/openapi.json")

logger = DefaultLogger("OrchestrationService").get_logger()

@app.get("/test/")
async def test_service():
    channel = RabbitMQConnection.get_channel()
    logger.info("Channel obtained")
    declare_exchange_queues(channel)
    logger.info("Queues and Exchange declared")


if __name__ == "__main__":
    logger.info("Starting Orchestration Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
