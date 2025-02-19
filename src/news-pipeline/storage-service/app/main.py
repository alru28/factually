from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models import Article, Source
from app.db.database import db
import uvicorn
from pymongo.errors import DuplicateKeyError, BulkWriteError
from bson import ObjectId
from app.utils.logger import DefaultLogger

logger = DefaultLogger("StorageService").get_logger()

app = FastAPI(title="Storage Service", openapi_url="/openapi.json")

async def create_indexes():
    logger.info("Creating unique indexes for articles and sources")
    await db["articles"].create_index("Link", unique=True)
    await db["sources"].create_index("base_url", unique=True)

@app.on_event("startup")
async def startup_event():
    logger.info("Startup event: Initializing indexes")
    await create_indexes()

# HELPER FUNCTIONS
def article_helper(article) -> Article:
    article["id"] = str(article["_id"])
    del article["_id"]
    return Article.parse_obj(article)

def source_helper(source) -> Source:
    source["id"] = str(source["_id"])
    del source["_id"]
    return Source.parse_obj(source)

# --------- Article Endpoints ---------
@app.post("/articles/", response_model=Article, status_code=201)
async def create_article(article: Article):
    logger.info("Received request to create an article")
    article_data = jsonable_encoder(article)
    try:
        new_article = await db["articles"].insert_one(article_data)
        logger.debug(f"Inserted article with _id: {new_article.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate article insertion attempted", exc_info=True)
        raise HTTPException(status_code=400, detail="Article with this Link already exists")
    created_article = await db["articles"].find_one({"_id": new_article.inserted_id})
    logger.info("Article created successfully")
    return article_helper(created_article)

# @app.post("/articles/bulk", response_model=List[Article], status_code=201)
# async def create_articles_bulk(articles: List[Article]):
#     logger.info("Received bulk articles creation request")
#     articles_data = [jsonable_encoder(article) for article in articles]
#     try:
#         result = await db["articles"].insert_many(articles_data, ordered=False)
#         logger.debug(f"Bulk inserted {len(result.inserted_ids)} articles")
#     except DuplicateKeyError:
#         logger.error("Duplicate key error in bulk article insertion", exc_info=True)
#         raise HTTPException(status_code=400, detail="One or more articles already exist")
#     except BulkWriteError as bwe:
#         logger.error("Bulk write error occurred", exc_info=True)
#         raise HTTPException(status_code=400, detail="One or more articles already exist")
#     created_articles = []
#     for _id in result.inserted_ids:
#         article_doc = await db["articles"].find_one({"_id": _id})
#         created_articles.append(article_helper(article_doc))
#     logger.info("Bulk article insertion completed successfully")
#     return created_articles

@app.post("/articles/bulk", response_model=List[Article], status_code=201)
async def create_articles_bulk(articles: List[Article]):
    logger.info("Received bulk articles creation request")
    articles_data = [jsonable_encoder(article) for article in articles]
    try:
        result = await db["articles"].insert_many(articles_data, ordered=False)
        logger.debug(f"Bulk inserted {len(result.inserted_ids)} articles")
    except DuplicateKeyError:
        logger.error("Duplicate key error in bulk article insertion", exc_info=True)
        raise HTTPException(status_code=400, detail="One or more articles already exist")
    except BulkWriteError as bwe:
        # GET THE DUPLICATED ONES, ERROR LOG THEM, AND MIMIC GOOD RESULT WITH THE REST
        duplicate_ids = [
            error["op"].get("_id")
            for error in bwe.details.get("writeErrors", [])
            if error.get("code") == 11000
        ]
        logger.error(
            f"Bulk write error occurred: {len(duplicate_ids)} duplicate articles: {duplicate_ids}",
            exc_info=False
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
    logger.info(f"Bulk article insertion completed successfully. Inserted {len(created_articles)} articles")
    return created_articles


@app.get("/articles/", response_model=List[Article])
async def list_articles():
    logger.info("Received request to list all articles")
    articles = []
    async for article in db["articles"].find():
        articles.append(article_helper(article))
    logger.debug(f"Retrieved {len(articles)} articles")
    return articles

@app.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    logger.info(f"Received request for article with id: {article_id}")
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if article is None:
        logger.error(f"Article with id {article_id} not found")
        raise HTTPException(status_code=404, detail="Article not found")
    logger.debug(f"Article retrieved: {article}")
    return article_helper(article)

@app.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article: Article):
    logger.info(f"Received request to update article with id: {article_id}")
    article_data = jsonable_encoder(article)
    result = await db["articles"].update_one({"_id": ObjectId(article_id)}, {"$set": article_data})
    if result.modified_count == 1:
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        logger.info(f"Article with id {article_id} updated successfully")
        return article_helper(updated_article)
    else:
        logger.error(f"Article with id {article_id} not found for update")
        raise HTTPException(status_code=404, detail="Article not found")

@app.delete("/articles/{article_id}", status_code=204)
async def delete_article(article_id: str):
    logger.info(f"Received request to delete article with id: {article_id}")
    result = await db["articles"].delete_one({"_id": ObjectId(article_id)})
    if result.deleted_count == 1:
        logger.info(f"Article with id {article_id} deleted successfully")
        return
    else:
        logger.error(f"Article with id {article_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Article not found")

# --------- Source Endpoints ---------
@app.post("/sources/", response_model=Source, status_code=201)
async def create_source(source: Source):
    logger.info("Received request to create a source")
    source_data = jsonable_encoder(source)
    try:
        new_source = await db["sources"].insert_one(source_data)
        logger.debug(f"Inserted source with _id: {new_source.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate source insertion attempted", exc_info=True)
        raise HTTPException(status_code=400, detail="Source with this base_url already exists")
    created_source = await db["sources"].find_one({"_id": new_source.inserted_id})
    logger.info("Source created successfully")
    return source_helper(created_source)

@app.get("/sources/", response_model=List[Source])
async def list_sources():
    logger.info("Received request to list all sources")
    sources_list = []
    async for source in db["sources"].find():
        sources_list.append(source_helper(source))
    logger.debug(f"Retrieved {len(sources_list)} sources")
    return sources_list

@app.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str):
    logger.info(f"Received request for source with id: {source_id}")
    source = await db["sources"].find_one({"_id": ObjectId(source_id)})
    if source is None:
        logger.error(f"Source with id {source_id} not found")
        raise HTTPException(status_code=404, detail="Source not found")
    logger.debug(f"Source retrieved: {source['name']}")
    return source_helper(source)

@app.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source: Source):
    logger.info(f"Received request to update source with id: {source_id}")
    source_data = jsonable_encoder(source)
    result = await db["sources"].update_one({"_id": ObjectId(source_id)}, {"$set": source_data})
    if result.modified_count == 1:
        updated_source = await db["sources"].find_one({"_id": ObjectId(source_id)})
        logger.info(f"Source with id {source_id} updated successfully")
        return source_helper(updated_source)
    else:
        logger.error(f"Source with id {source_id} not found for update")
        raise HTTPException(status_code=404, detail="Source not found")

@app.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str):
    logger.info(f"Received request to delete source with id: {source_id}")
    result = await db["sources"].delete_one({"_id": ObjectId(source_id)})
    if result.deleted_count == 1:
        logger.info(f"Source with id {source_id} deleted successfully")
        return
    else:
        logger.error(f"Source with id {source_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Source not found")

if __name__ == "__main__":
    logger.info("Starting Storage Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
