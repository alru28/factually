import os
import httpx
from typing import List
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger
from app.models import SearchResult


logger = DefaultLogger("VerificationService").get_logger()

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")

async def search_articles(query: str, retrieve_params: dict = None) -> List[SearchResult]:
    """
    Performs a search for articles in the Storage Service based on a query.
    
    Args:
        query (str): The search query string.
        retrieve_params (dict, optional): Additional parameters for the storage service.
    
    Returns:
        dict: The article data retrieved from the Storage Service.
    
    Raises:
        Exception: If the search/retrieval fails.
    """
    logger.debug(f"Searching articles with query: {query}")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/search/", params={"query": query, **(retrieve_params or {})})
        if response.status_code != 200:
            logger.error(f"Failed to search articles: {response.text}")
            raise Exception(f"Failed to search articles")
        articles = response.json()
        logger.debug(f"Retrieved {len(articles)} articles successfully")
        return articles