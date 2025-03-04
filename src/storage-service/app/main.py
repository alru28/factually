from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models import Article, Source, SearchResult, article_helper, source_helper
from app.db.mongo import db
from app.db.weaviate_client import create_article_schema, get_weaviate_client, sync_articles_to_weaviate
import requests
import uvicorn
import os
from pymongo.errors import DuplicateKeyError, BulkWriteError
import uuid
from app.utils.logger import DefaultLogger

OLLAMA_CONNECTION_STRING = os.getenv(
    "OLLAMA_CONNECTION_STRING", "http://ollama:11434"
)

logger = DefaultLogger("StorageService").get_logger()

def check_and_pull_model():
    try:
        response = requests.get(f"{OLLAMA_CONNECTION_STRING}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"MODELOS: {models}")
            if "llama3.2:1b" not in models:
                pull_response = requests.post(f"{OLLAMA_CONNECTION_STRING}/api/pull", json={"name": "llama3.2:1b"})
                if pull_response.status_code != 200:
                    raise Exception("Failed to pull llama2 model")
            if "nomic-embed-text" not in models:
                pull_response = requests.post(f"{OLLAMA_CONNECTION_STRING}/api/pull", json={"name": "nomic-embed-text"})
                if pull_response.status_code != 200:
                    raise Exception("Failed to pull nomic-embed-text model")
        else:
            raise Exception("Failed to retrieve models from Ollama")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_indexes():
    """
    Creates unique indexes for the articles and sources collections in the database.

    This function ensures that each article's 'Link' field and each source's 'base_url' field is unique,
    preventing duplicate entries.
    """
    logger.info("Creating unique indexes for articles and sources")
    await db["articles"].create_index("Link", unique=True)
    await db["sources"].create_index("base_url", unique=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Models and DBs init
    logger.info("Startup event: Initializing MongoDB indexes")
    await create_indexes()
    logger.info("Startup event: Initializing Ollama models")
    check_and_pull_model()
    logger.info("Startup event: Initializing Weaviate schema")
    create_article_schema()    
    # App running
    yield

app = FastAPI(lifespan=lifespan, title="Storage Service", openapi_url="/openapi.json")

@app.post("/articles/", response_model=Article, status_code=201)
async def create_article(article: Article, background_tasks: BackgroundTasks):
    """
    Creates a new article in the database.
    """
    logger.info("Received request to create an article")
    article_data = jsonable_encoder(article)
    
    if "id" in article_data:
        try:
            valid_id = str(uuid.UUID(article_data['id']))
        except ValueError:
            logger.error(f"Invalid article id format: {article_data['id']}")
            raise HTTPException(status_code=400, detail="Invalid article id format.")
        article_data["_id"] = article_data.pop("id")
    try:
        new_article = await db["articles"].insert_one(article_data)
        logger.debug(f"Inserted article with id: {new_article.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate article insertion attempted", exc_info=True)
        raise HTTPException(
            status_code=400, detail="Article with this Link already exists"
        )
    created_article = await db["articles"].find_one({"_id": new_article.inserted_id})
    article_obj = article_helper(created_article)
    background_tasks.add_task(sync_articles_to_weaviate, [article_obj])
    logger.info("Article created and synced with weaviate successfully")
    return article_obj

@app.post("/articles/bulk", response_model=List[Article], status_code=201)
async def create_articles_bulk(articles: List[Article], background_tasks: BackgroundTasks):
    """
    Creates multiple articles in bulk.
    """
    logger.info("Received bulk articles creation request")
    articles_data = [jsonable_encoder(article) for article in articles]
    for article_data in articles_data:
        if "id" in article_data:
            try:
                valid_id = str(uuid.UUID(article_data['id']))
            except ValueError:
                logger.error(f"Invalid article id format: {article_data['id']}")
                raise HTTPException(status_code=400, detail="Invalid article id format.")
            article_data["_id"] = article_data.pop("id")
        
    try:
        result = await db["articles"].insert_many(articles_data, ordered=False)
        logger.debug(f"Bulk inserted {len(result.inserted_ids)} articles")
    except DuplicateKeyError:
        logger.error("Duplicate key error in bulk article insertion", exc_info=True)
        raise HTTPException(
            status_code=400, detail="One or more articles already exist"
        )
    except BulkWriteError as bwe:
        duplicate_ids = [
            error["op"].get("_id")
            for error in bwe.details.get("writeErrors", [])
            if error.get("code") == 11000
        ]
        logger.error(
            f"Bulk write error occurred: {len(duplicate_ids)} duplicate articles: {duplicate_ids}",
            exc_info=False,
        )
        inserted_ids = list(bwe.details.get("insertedIds", {}).values())
        class DummyResult:
            pass
        result = DummyResult()
        result.inserted_ids = inserted_ids

    created_articles = []
    for _id in result.inserted_ids:
        article_doc = await db["articles"].find_one({"_id": _id})
        created_articles.append(article_helper(article_doc))
    logger.info(
        f"Bulk article insertion completed successfully. Inserted {len(created_articles)} articles"
    )
    background_tasks.add_task(sync_articles_to_weaviate, created_articles)
    return created_articles

@app.get("/articles/", response_model=List[Article])
async def list_articles():
    """
    Retrieves a list of all articles from the database.
    """
    logger.info("Received request to list all articles")
    articles = []
    async for article in db["articles"].find():
        articles.append(article_helper(article))
    logger.debug(f"Retrieved {len(articles)} articles")
    return articles

@app.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """
    Retrieves a single article by its ID.
    """
    logger.info(f"Received request for article with id: {article_id}")
    try:
        valid_id = str(uuid.UUID(article_id))
    except ValueError:
        logger.error(f"Invalid article id format: {article_id}")
        raise HTTPException(status_code=400, detail="Invalid article id format.")
    article = await db["articles"].find_one({"_id": valid_id})
    if article is None:
        logger.error(f"Article with id {article_id} not found")
        raise HTTPException(status_code=404, detail="Article not found")
    logger.debug(f"Article retrieved: {article}")
    return article_helper(article)

@app.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article: Article):
    """
    Updates an existing article identified by its ID.
    """
    logger.info(f"Received request to update article with id: {article_id}")
    try:
        valid_id = str(uuid.UUID(article_id))
    except ValueError:
        logger.error(f"Invalid article id format: {article_id}")
        raise HTTPException(status_code=400, detail="Invalid article id format.")
    article_data = jsonable_encoder(article)
    result = await db["articles"].update_one(
        {"_id": valid_id}, {"$set": article_data}
    )
    if result.modified_count == 1:
        updated_article = await db["articles"].find_one({"_id": valid_id})
        logger.info(f"Article with id {article_id} updated successfully")
        return article_helper(updated_article)
    else:
        logger.error(f"Article with id {article_id} not found for update")
        raise HTTPException(status_code=404, detail="Article not found")

@app.delete("/articles/{article_id}", status_code=204)
async def delete_article(article_id: str):
    """
    Deletes an article by its ID.
    """
    logger.info(f"Received request to delete article with id: {article_id}")
    try:
        valid_id = str(uuid.UUID(article_id))
    except ValueError:
        logger.error(f"Invalid article id format: {article_id}")
        raise HTTPException(status_code=400, detail="Invalid article id format.")
    result = await db["articles"].delete_one({"_id": valid_id})
    if result.deleted_count == 1:
        logger.info(f"Article with id {article_id} deleted successfully")
        return
    else:
        logger.error(f"Article with id {article_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Article not found")

@app.post("/sources/", response_model=Source, status_code=201)
async def create_source(source: Source):
    """
    Creates a new source in the database.
    """
    logger.info("Received request to create a source")
    source_data = jsonable_encoder(source)
    if "id" in source_data:
        try:
            valid_id = str(uuid.UUID(source_data['id']))
        except ValueError:
            logger.error(f"Invalid source id format: {source_data['id']}")
            raise HTTPException(status_code=400, detail="Invalid source id format.")
        source_data["_id"] = source_data.pop("id")
    try:
        new_source = await db["sources"].insert_one(source_data)
        logger.debug(f"Inserted source with _id: {new_source.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate source insertion attempted", exc_info=True)
        raise HTTPException(
            status_code=400, detail="Source with this base_url already exists"
        )
    created_source = await db["sources"].find_one({"_id": new_source.inserted_id})
    logger.info("Source created successfully")
    return source_helper(created_source)

@app.get("/sources/", response_model=List[Source])
async def list_sources():
    """
    Retrieves a list of all sources from the database.
    """
    logger.info("Received request to list all sources")
    sources_list = []
    async for source in db["sources"].find():
        sources_list.append(source_helper(source))
    logger.debug(f"Retrieved {len(sources_list)} sources")
    return sources_list

@app.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str):
    """
    Retrieves a single source by its ID.
    """
    logger.info(f"Received request for source with id: {source_id}")
    try:
        valid_id = str(uuid.UUID(source_id))
    except ValueError:
        logger.error(f"Invalid source id format: {source_id}")
        raise HTTPException(status_code=400, detail="Invalid source id format.")
    source = await db["sources"].find_one({"_id": valid_id})
    if source is None:
        logger.error(f"Source with id {source_id} not found")
        raise HTTPException(status_code=404, detail="Source not found")
    logger.debug(f"Source retrieved: {source['name']}")
    return source_helper(source)

@app.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source: Source):
    """
    Updates an existing source identified by its ID.
    """
    logger.info(f"Received request to update source with id: {source_id}")
    try:
        valid_id = str(uuid.UUID(source_id))
    except ValueError:
        logger.error(f"Invalid source id format: {source_id}")
        raise HTTPException(status_code=400, detail="Invalid source id format.")
    source_data = jsonable_encoder(source)
    result = await db["sources"].update_one(
        {"_id": valid_id}, {"$set": source_data}
    )
    if result.modified_count == 1:
        updated_source = await db["sources"].find_one({"_id": valid_id})
        logger.info(f"Source with id {source_id} updated successfully")
        return source_helper(updated_source)
    else:
        logger.error(f"Source with id {source_id} not found for update")
        raise HTTPException(status_code=404, detail="Source not found")

@app.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str):
    """
    Deletes a source by its ID.
    """
    logger.info(f"Received request to delete source with id: {source_id}")
    try:
        valid_id = str(uuid.UUID(source_id))
    except ValueError:
        logger.error(f"Invalid source id format: {source_id}")
        raise HTTPException(status_code=400, detail="Invalid source id format.")
    result = await db["sources"].delete_one({"_id": valid_id})
    if result.deleted_count == 1:
        logger.info(f"Source with id {source_id} deleted successfully")
        return
    else:
        logger.error(f"Source with id {source_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Source not found")

@app.get("/search/", response_model=List[SearchResult])
async def search_articles(query: str, alpha: float = 0.5, limit: int = 5):
    """
    Search articles using Weaviate's hybrid search.
    """
    client = get_weaviate_client()
    articles = client.collections.get('Article')
    response = articles.query.hybrid(
        query=query,
        alpha=alpha,
        limit=limit
    )

    results = []
    for article in response.objects:
        results.append({
            'Title': article.properties.title,
            'Date': article.properties.date,
            'Content': article.properties.content,
            'Source': article.properties.source
        })
    client.close()
    return results

@app.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connectivity issue: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Storage Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
