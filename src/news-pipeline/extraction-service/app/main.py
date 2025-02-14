from datetime import datetime, timedelta
from app.core.scrapper import scrape_articles_base, scrape_articles_content
from app.utils.storage import store_articles_to_json
from app.utils.date_formatter import format_date_str
from app.config import sources
from app.models import ScrapeRequest, SourceScrapeRequest
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

import httpx
import os

app = FastAPI(title="Extraction Service")

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8000")

@app.post("/scrape/source", response_model=dict)
async def scrape_source(scrape_request: SourceScrapeRequest):
    """
    Scrapes a specific source (provided in the request) from date_base to date_cutoff.
    The scraped articles are then inserted into the storage service via its bulk API.
    """
    date_base = format_date_str(scrape_request.date_base, "%d-%m-%Y")
    date_cutoff = format_date_str(scrape_request.date_cutoff, "%d-%m-%Y")

    articles = scrape_articles_base(scrape_request.name, date_base, date_cutoff)
    
    articles_content = scrape_articles_content(articles)

    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(articles_content)
        content_resp = await client.post(
            f"{STORAGE_SERVICE_URL}/articles/bulk", json=payload
        )
        if content_resp.status_code != 201:
            raise HTTPException(
                status_code=500,
                detail="Error inserting content articles for source."
            )

    return {"message": f"Scraped and inserted articles for source {scrape_request.name}"}

@app.post("/scrape/all", response_model=dict)
async def scrape_all(scrape_request: ScrapeRequest):
    """
    Retrieves all sources from the storage service, scrapes articles for each source
    from date_base to date_cutoff, and then inserts the scraped articles into the storage service.
    """
    date_base = format_date_str(scrape_request.date_base, "%d-%m-%Y")
    date_cutoff = format_date_str(scrape_request.date_cutoff, "%d-%m-%Y")

    async with httpx.AsyncClient() as client:
        sources_resp = await client.get(f"{STORAGE_SERVICE_URL}/sources/")
        if sources_resp.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Error retrieving sources from storage service."
            )
        sources = sources_resp.json()

    all_articles = []
    
    for source in sources:
        source_name = source.get("name")
        if source_name:
            articles = scrape_articles_base(source_name, date_base, date_cutoff)
            all_articles.extend(articles)

    articles_content = scrape_articles_content(all_articles)

    async with httpx.AsyncClient() as client:
        payload = jsonable_encoder(articles_content)
        content_resp = await client.post(
            f"{STORAGE_SERVICE_URL}/articles/bulk", json=payload
        )
        if content_resp.status_code != 201:
            raise HTTPException(
                status_code=500,
                detail="Error inserting content articles for all sources."
            )

    return {"message": "Scraped and inserted articles for all sources"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)