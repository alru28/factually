from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from app.core.scraper import scrape_articles_base, scrape_articles_content
from app.utils.date_formatter import format_date_str, secure_date_range
from app.models import ScrapeRequest, SourceScrapeRequest
from app.utils.logger import DefaultLogger
from app.utils.services import get_sources, post_articles_bulk
from fastapi import FastAPI, HTTPException
from app.rabbitmq.client import get_rabbitmq_client
from app.rabbitmq.operations import handle_message
import asyncio
import uvicorn

logger = DefaultLogger("ExtractionService").get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client = await get_rabbitmq_client()
        logger.info("RabbitMQ Client connected | Queues and Exchange declared")

        asyncio.create_task(client.consume('tasks_extraction', callback=handle_message))
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

app = FastAPI(lifespan=lifespan, title="Extraction Service")

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
    date_base, date_cutoff = secure_date_range(
        scrape_request.date_base, scrape_request.date_cutoff
    )

    try:
        sources_list = await get_sources()
    except Exception as e:
        logger.error(f"Error retrieving sources from storage service: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sources from storage service.")
    
    source_dict = next(
        (src for src in sources_list if src.get("name", "").lower() == scrape_request.name.lower()),
        None
    )
    if not source_dict:
        logger.error(f"Source '{scrape_request.name}' not found in storage service")
        raise HTTPException(status_code=404, detail=f"Source '{scrape_request.name}' not found in storage service.")
    
    logger.info(f"Found source configuration for {scrape_request.name}: {source_dict}")

    articles = scrape_articles_base(source_dict, date_base, date_cutoff)
    logger.debug(f"Scraped {len(articles)} base articles")

    articles_content = scrape_articles_content(articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    try:
        await post_articles_bulk(articles_content)
    except Exception as e:
        logger.error(f"Error posting articles: {e}")
        raise HTTPException(status_code=500, detail="Error inserting content articles for source.")

    logger.info(f"Scrape and insertion completed for source {scrape_request.name}")
    return {
        "message": f"Scraped and inserted articles for source {scrape_request.name}"
    }


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
        logger.debug(
            "date_base equals date_cutoff; adjusting cutoff by subtracting 1 day"
        )
        date_cutoff = date_base - timedelta(days=1)

    try:
        sources_list = await get_sources()
    except Exception as e:
        logger.error(f"Error retrieving sources from storage service: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sources from storage service.")

    all_articles = []
    for source in sources_list:
        if source.get("name"):
            logger.info(f"Scraping articles for source: {source.get('name')}")
            articles = scrape_articles_base(source, date_base, date_cutoff)
            logger.debug(
                f"Scraped {len(articles)} articles for source {source.get('name')}"
            )
            all_articles.extend(articles)

    logger.info("Scraping content for all scraped articles")
    articles_content = scrape_articles_content(all_articles)
    logger.debug(f"Scraped content for {len(articles_content)} articles")

    try:
        await post_articles_bulk(articles_content)
    except Exception as e:
        logger.error(f"Error posting articles: {e}")
        raise HTTPException(status_code=500, detail="Error inserting content articles for all sources.")

    logger.info("Scrape and insertion completed for all sources")
    return {"message": "Scraped and inserted articles for all sources"}

if __name__ == "__main__":
    logger.info("Starting Extraction Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
