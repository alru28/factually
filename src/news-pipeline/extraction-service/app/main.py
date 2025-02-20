from datetime import datetime, timedelta
from app.core.scrapper import scrape_articles_base, scrape_articles_content
from app.utils.date_formatter import format_date_str
from app.models import ScrapeRequest, SourceScrapeRequest
from app.utils.logger import DefaultLogger
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

import httpx
import os
import uvicorn

logger = DefaultLogger("ExtractionService").get_logger()

app = FastAPI(title="Extraction Service")

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")

def secure_date_range(date_base_str: str, date_cutoff_str: str):
    """
    Adjusts the date range provided in string format.

    Converts the given base date and cutoff date strings into datetime objects using a specific format.
    If both dates are identical, it subtracts one day from the cutoff date to ensure a proper range.

    Args:
        date_base_str (str): Base date in string format.
        date_cutoff_str (str): Cutoff date in string format.

    Returns:
        tuple: A tuple containing the base date and the adjusted cutoff date as datetime objects.
    """
    date_base = format_date_str(date_base_str, "%d-%m-%Y")
    date_cutoff = format_date_str(date_cutoff_str, "%d-%m-%Y")
    if date_base == date_cutoff:
        date_cutoff = date_base - timedelta(days=1)
    return date_base, date_cutoff

@app.post("/scrape/source", response_model=dict)
async def scrape_source(scrape_request: SourceScrapeRequest):
    """
    Scrapes a specific source based on the provided source name and date range.

    This endpoint retrieves the source configuration from the storage service,
    scrapes the base articles using the source configuration and date range,
    then scrapes article contents, and finally posts the scraped content to the storage service.

    Args:
        scrape_request (SourceScrapeRequest): Request object containing the source name, base date, and cutoff date.

    Returns:
        dict: A message indicating successful scraping and insertion of articles for the specified source.

    Raises:
        HTTPException: If sources cannot be retrieved or if the specified source is not found, or if posting content fails.
    """
    logger.info(f"Received scrape/source request for source: {scrape_request.name}")
    date_base, date_cutoff = secure_date_range(scrape_request.date_base, scrape_request.date_cutoff)

    async with httpx.AsyncClient() as client:
        logger.debug("Retrieving sources from storage service")
        sources_resp = await client.get(f"{STORAGE_SERVICE_URL}/sources/")
        if sources_resp.status_code != 200:
            logger.error("Failed to retrieve sources from storage service")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving sources from storage service."
            )
        sources_list = sources_resp.json()
        logger.debug(f"Retrieved {len(sources_list)} sources")

    source_dict = next(
        (src for src in sources_list if src.get("name", "").lower() == scrape_request.name.lower()),
        None
    )
    if not source_dict:
        logger.error(f"Source '{scrape_request.name}' not found in storage service")
        raise HTTPException(
            status_code=404,
            detail=f"Source '{scrape_request.name}' not found in storage service."
        )
    logger.info(f"Found source configuration for {scrape_request.name}: {source_dict}")
    
    articles = scrape_articles_base(source_dict, date_base, date_cutoff)
    logger.debug(f"Scraped {len(articles)} base articles")
    
    articles_content = scrape_articles_content(articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(articles_content)
        logger.debug("Posting scraped article content to storage service")
        content_resp = await client.post(
            f"{STORAGE_SERVICE_URL}/articles/bulk", json=payload
        )
        if content_resp.status_code != 201:
            logger.error("Error inserting content articles for source")
            raise HTTPException(
                status_code=500,
                detail="Error inserting content articles for source."
            )

    logger.info(f"Scrape and insertion completed for source {scrape_request.name}")
    return {"message": f"Scraped and inserted articles for source {scrape_request.name}"}

@app.post("/scrape/all", response_model=dict)
async def scrape_all(scrape_request: ScrapeRequest):
    """
    Scrapes articles for all sources based on the provided date range.

    This endpoint retrieves all source configurations from the storage service,
    scrapes base articles for each source using the specified date range,
    then scrapes article contents for all scraped articles,
    and finally posts the collected articles to the storage service.

    Args:
        scrape_request (ScrapeRequest): Request object containing the base date and cutoff date.

    Returns:
        dict: A message indicating successful scraping and insertion of articles for all sources.

    Raises:
        HTTPException: If sources cannot be retrieved or if posting content fails.
    """
    logger.info("Received scrape/all request")
    date_base = format_date_str(scrape_request.date_base, "%d-%m-%Y")
    date_cutoff = format_date_str(scrape_request.date_cutoff, "%d-%m-%Y")

    if date_base == date_cutoff:
        logger.debug("date_base equals date_cutoff; adjusting cutoff by subtracting 1 day")
        date_cutoff = date_base - timedelta(days=1)

    async with httpx.AsyncClient() as client:
        logger.debug("Retrieving sources from storage service for scrape/all")
        sources_resp = await client.get(f"{STORAGE_SERVICE_URL}/sources/")
        if sources_resp.status_code != 200:
            logger.error("Error retrieving sources from storage service for scrape/all")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving sources from storage service."
            )
        sources_list = sources_resp.json()
        logger.debug(f"Retrieved {len(sources_list)} sources for scrape/all")

    all_articles = []
    for source in sources_list:
        if source.get("name"):
            logger.info(f"Scraping articles for source: {source.get('name')}")
            articles = scrape_articles_base(source, date_base, date_cutoff)
            logger.debug(f"Scraped {len(articles)} articles for source {source.get('name')}")
            all_articles.extend(articles)

    logger.info("Scraping content for all scraped articles")
    articles_content = scrape_articles_content(all_articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(articles_content)
        logger.debug("Posting scraped article content for all sources to storage service")
        content_resp = await client.post(
            f"{STORAGE_SERVICE_URL}/articles/bulk", json=payload
        )
        if content_resp.status_code != 201:
            logger.error("Error inserting content articles for all sources")
            raise HTTPException(
                status_code=500,
                detail="Error inserting content articles for all sources."
            )

    logger.info("Scrape and insertion completed for all sources")
    return {"message": "Scraped and inserted articles for all sources"}

if __name__ == "__main__":
    logger.info("Starting Extraction Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
