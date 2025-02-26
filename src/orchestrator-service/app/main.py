from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger
import uvicorn

app = FastAPI(title="OrchestrationService", openapi_url="/openapi.json")

logger = DefaultLogger("OrchestrationService").get_logger()

if __name__ == "__main__":
    logger.info("Starting Orchestration Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
