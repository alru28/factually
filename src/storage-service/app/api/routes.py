from fastapi import APIRouter, HTTPException, BackgroundTasks
from pymongo.errors import DuplicateKeyError, BulkWriteError
from fastapi.encoders import jsonable_encoder
from typing import List
import uuid
from app.models import Article, Source, SearchResult, SearchRequest, article_helper, source_helper
from app.db.mongo import MongoClientSingleton
from app.db.weaviate_client import WeaviateAsyncClientSingleton, sync_articles_to_weaviate
from app.utils.logger import DefaultLogger

router = APIRouter()
logger = DefaultLogger().get_logger()

@router.post("/articles", response_model=Article, status_code=201)
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
        new_article = await MongoClientSingleton.get_db()["articles"].insert_one(article_data)
        logger.debug(f"Inserted article with id: {new_article.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate article insertion attempted", exc_info=True)
        raise HTTPException(
            status_code=400, detail="Article with this Link already exists"
        )
    created_article = await MongoClientSingleton.get_db()["articles"].find_one({"_id": new_article.inserted_id})
    article_obj = article_helper(created_article)
    background_tasks.add_task(sync_articles_to_weaviate, [article_obj])
    logger.info("Article created and synced with weaviate successfully")
    return article_obj

@router.post("/articles/bulk", response_model=List[Article], status_code=201)
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
        result = await MongoClientSingleton.get_db()["articles"].insert_many(articles_data, ordered=False)
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
        article_doc = await MongoClientSingleton.get_db()["articles"].find_one({"_id": _id})
        created_articles.append(article_helper(article_doc))
    logger.info(
        f"Bulk article insertion completed successfully. Inserted {len(created_articles)} articles"
    )
    background_tasks.add_task(sync_articles_to_weaviate, created_articles)
    return created_articles

@router.get("/articles", response_model=List[Article])
async def list_articles():
    """
    Retrieves a list of all articles from the database.
    """
    logger.info("Received request to list all articles")
    articles = []
    async for article in MongoClientSingleton.get_db()["articles"].find():
        articles.append(article_helper(article))
    logger.debug(f"Retrieved {len(articles)} articles")
    return articles

@router.get("/articles/{article_id}", response_model=Article)
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
    article = await MongoClientSingleton.get_db()["articles"].find_one({"_id": valid_id})
    if article is None:
        logger.error(f"Article with id {article_id} not found")
        raise HTTPException(status_code=404, detail="Article not found")
    logger.debug(f"Article retrieved: {article_id}")
    return article_helper(article)

@router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article: Article, background_tasks: BackgroundTasks):
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
    result = await MongoClientSingleton.get_db()["articles"].update_one(
        {"_id": valid_id}, {"$set": article_data}
    )
    if result.modified_count == 1:
        updated_article = await MongoClientSingleton.get_db()["articles"].find_one({"_id": valid_id})
        background_tasks.add_task(sync_articles_to_weaviate, [updated_article])
        logger.info(f"Article with id {article_id} updated successfully")
        return article_helper(updated_article)
    else:
        logger.error(f"Article with id {article_id} not found for update")
        raise HTTPException(status_code=404, detail="Article not found")

@router.delete("/articles/{article_id}", status_code=204)
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
    result = await MongoClientSingleton.get_db()["articles"].delete_one({"_id": valid_id})
    if result.deleted_count == 1:
        logger.info(f"Article with id {article_id} deleted successfully")
        return
    else:
        logger.error(f"Article with id {article_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Article not found")

@router.post("/sources", response_model=Source, status_code=201)
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
        new_source = await MongoClientSingleton.get_db()["sources"].insert_one(source_data)
        logger.debug(f"Inserted source with _id: {new_source.inserted_id}")
    except DuplicateKeyError:
        logger.error("Duplicate source insertion attempted", exc_info=True)
        raise HTTPException(
            status_code=400, detail="Source with this base_url already exists"
        )
    created_source = await MongoClientSingleton.get_db()["sources"].find_one({"_id": new_source.inserted_id})
    logger.info("Source created successfully")
    return source_helper(created_source)

@router.get("/sources", response_model=List[Source])
async def list_sources():
    """
    Retrieves a list of all sources from the database.
    """
    logger.info("Received request to list all sources")
    sources_list = []
    async for source in MongoClientSingleton.get_db()["sources"].find():
        sources_list.append(source_helper(source))
    logger.debug(f"Retrieved {len(sources_list)} sources")
    return sources_list

@router.get("/sources/{source_id}", response_model=Source)
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
    source = await MongoClientSingleton.get_db()["sources"].find_one({"_id": valid_id})
    if source is None:
        logger.error(f"Source with id {source_id} not found")
        raise HTTPException(status_code=404, detail="Source not found")
    logger.debug(f"Source retrieved: {source['name']}")
    return source_helper(source)

@router.put("/sources/{source_id}", response_model=Source)
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
    result = await MongoClientSingleton.get_db()["sources"].update_one(
        {"_id": valid_id}, {"$set": source_data}
    )
    if result.modified_count == 1:
        updated_source = await MongoClientSingleton.get_db()["sources"].find_one({"_id": valid_id})
        logger.info(f"Source with id {source_id} updated successfully")
        return source_helper(updated_source)
    else:
        logger.error(f"Source with id {source_id} not found for update")
        raise HTTPException(status_code=404, detail="Source not found")

@router.delete("/sources/{source_id}", status_code=204)
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
    result = await MongoClientSingleton.get_db()["sources"].delete_one({"_id": valid_id})
    if result.deleted_count == 1:
        logger.info(f"Source with id {source_id} deleted successfully")
        return
    else:
        logger.error(f"Source with id {source_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Source not found")

@router.post("/search", response_model=List[SearchResult])
async def search_articles(request: SearchRequest):
    """
    Search articles using Weaviate's hybrid search.
    """
    articles = WeaviateAsyncClientSingleton.get_client().collections.get('Article')
    response = await articles.query.hybrid(
        query=request.query,
        alpha=request.alpha,
        limit=request.limit
    )

    results = []
    for article in response.objects:
        results.append({
            'Title': article.properties['title'],
            'Date': article.properties['date'],
            'Content': article.properties['content'],
            'Source': article.properties['source'],
            'Summary': article.properties['summary'],
            'Sentiment': article.properties['sentiment'],
            'Classification': article.properties['classification'],
        })
    return results

@router.get("/health")
async def health_check():
    try:
        await MongoClientSingleton.get_db().command("ping")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connectivity issue: {str(e)}")