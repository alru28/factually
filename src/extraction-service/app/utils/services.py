# app/utils/services.py

import os
import httpx
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger

logger = DefaultLogger("ExtractionService").get_logger()

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")
ORCHESTRATOR_SERVICE_URL = os.getenv("ORCHESTRATOR_SERVICE_URL", "http://orchestrator-service:8000")

async def get_sources():
    logger.debug("Requesting sources from Storage Service")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/sources/")
        if response.status_code != 200:
            logger.error("Failed to retrieve sources from Storage Service")
            raise Exception("Failed to retrieve sources")
        sources = response.json()
        logger.debug(f"Retrieved {len(sources)} sources")
        return sources

async def post_articles_bulk(articles):
    logger.debug("Posting articles in bulk to Storage Service")
    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(articles)
        response = await client.post(f"{STORAGE_SERVICE_URL}/articles/bulk", json=payload)
        if response.status_code != 201:
            logger.error("Error inserting articles into Storage Service")
            raise Exception("Error inserting articles")
        logger.info("Articles successfully inserted into Storage Service")
        return response.json()

async def notify_orchestrator(correlation_id: str, task_completion: dict):
    callback_url = f"{ORCHESTRATOR_SERVICE_URL}/api/workflows/{correlation_id}/complete"
    logger.debug(f"Notifying orchestrator at {callback_url} with payload: {task_completion}")
    async with httpx.AsyncClient() as client:
        response = await client.post(callback_url, json=task_completion)
        if response.status_code not in (200, 201):
            logger.error("Failed to notify orchestrator")
            raise Exception("Failed to notify orchestrator")
        logger.info("Orchestrator notified successfully")
        return response.json()
