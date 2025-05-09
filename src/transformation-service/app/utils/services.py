import os
import httpx
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger

logger = DefaultLogger().get_logger()

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")

async def retrieve_article(article_id: str) -> dict:
    """
    Retrieves an article from the Storage Service by its ID.
    
    Args:
        article_id (str): The UUID of the article.
    
    Returns:
        dict: The article data retrieved from the Storage Service.
    
    Raises:
        Exception: If the retrieval fails.
    """
    logger.debug(f"Requesting article {article_id} from Storage Service")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/articles/{article_id}")
        if response.status_code != 200:
            logger.error(f"Failed to retrieve article {article_id}: {response.text}")
            raise Exception(f"Failed to retrieve article {article_id}")
        article = response.json()
        logger.debug(f"Retrieved article {article_id} successfully")
        return article
    
async def retrieve_article_content(article_id: str) -> str:
        """
        Retrieves an article from the storage service by its ID and concatenates its title and paragraphs.
        
        Args:
            article_id (str): The unique identifier for the article to retrieve.
        
        Returns:
            str: A string containing the article's title and paragraphs.
        
        Raises:
            Exception: If the article retrieval fails (non-200 response).
        """
        logger.debug(f"Requesting article {article_id} from Storage Service")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STORAGE_SERVICE_URL}/articles/{article_id}")
            if response.status_code != 200:
                logger.error(f"Failed to retrieve article {article_id}: {response.text}")
                raise Exception(f"Failed to retrieve article {article_id}")
            article = response.json()
            title = article.get("Title", "")
            paragraphs = article.get("Paragraphs", [])
            content = title + "\n" + "\n".join(paragraphs)
            logger.debug(f"Retrieved article content {article_id} successfully")
            return content

async def update_article(article_id: str, updated_data: dict) -> dict:
    """
    Updates an article in the Storage Service with the provided data.
    
    Args:
        article_id (str): The UUID of the article.
        updated_data (dict): The updated article data.
    
    Returns:
        dict: The updated article data as returned by the Storage Service.
    
    Raises:
        Exception: If the update fails.
    """
    logger.debug(f"Updating article {article_id} in Storage Service")
    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(updated_data)
        response = await client.put(f"{STORAGE_SERVICE_URL}/articles/{article_id}", json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to update article {article_id}: {response.text}")
            raise Exception(f"Failed to update article {article_id}")
        article = response.json()
        logger.debug(f"Article {article_id} updated successfully")
        return article

async def store_processed_article(article_id: str, processed_fields: dict) -> dict:
    """
    Retrieves an article, merges in processed fields (e.g., summary, sentiment, classification),
    and updates the article in the Storage Service.
    
    Args:
        article_id (str): The UUID of the article.
        processed_fields (dict): A dictionary of fields to update in the article.
    
    Returns:
        dict: The updated article data with the enriched fields.
    """
    logger.info(f"Storing processed data for article {article_id}")
    article = await retrieve_article(article_id)
    
    article.update(processed_fields)
    
    updated_article = await update_article(article_id, article)
    logger.info(f"Processed article {article_id} stored successfully")
    return updated_article
