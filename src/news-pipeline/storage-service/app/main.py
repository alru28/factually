from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
from app.models import Article, Source
from app.db.database import db
import uvicorn
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

app = FastAPI(title="Storage Service", openapi_url="/openapi.json")

async def create_indexes():
    await db["articles"].create_index("Link", unique=True)
    await db["sources"].create_index("base_url", unique=True)

@app.on_event("startup")
async def startup_event():
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
    article_data = jsonable_encoder(article)
    try:
        new_article = await db["articles"].insert_one(article_data)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Article with this Link already exists")
    created_article = await db["articles"].find_one({"_id": new_article.inserted_id})
    return article_helper(created_article)

@app.post("/articles/bulk", response_model=List[Article], status_code=201)
async def create_articles_bulk(articles: List[Article]):
    articles_data = [jsonable_encoder(article) for article in articles]
    try:
        result = await db["articles"].insert_many(articles_data, ordered=False)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="One or more articles already exist")
    created_articles = []
    for _id in result.inserted_ids:
        article = await db["articles"].find_one({"_id": _id})
        created_articles.append(article_helper(article))
    return created_articles

@app.get("/articles/", response_model=List[Article])
async def list_articles():
    articles = []
    async for article in db["articles"].find():
        articles.append(article_helper(article))
    return articles

@app.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    article = await db["articles"].find_one({"_id": ObjectId(article_id)})
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article_helper(article)

@app.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article: Article):
    article = jsonable_encoder(article)
    result = await db["articles"].update_one({"_id": ObjectId(article_id)}, {"$set": article})
    if result.modified_count == 1:
        updated_article = await db["articles"].find_one({"_id": ObjectId(article_id)})
        return article_helper(updated_article)
    else:
        raise HTTPException(status_code=404, detail="Article not found")

@app.delete("/articles/{article_id}", status_code=204)
async def delete_article(article_id: str):
    result = await db["articles"].delete_one({"_id": ObjectId(article_id)})
    if result.deleted_count == 1:
        return
    else:
        raise HTTPException(status_code=404, detail="Article not found")

# --------- Source Endpoints ---------
@app.post("/sources/", response_model=Source, status_code=201)
async def create_source(source: Source):
    source_data = jsonable_encoder(source)
    try:
        new_source = await db["sources"].insert_one(source_data) # Micro-bug: You can create exactly 1 duplicate of the original sources
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Source with this base_url already exists")
    created_source = await db["sources"].find_one({"_id": new_source.inserted_id})
    return source_helper(created_source)

@app.get("/sources/", response_model=List[Source])
async def list_sources():
    sources = []
    async for source in db["sources"].find():
        sources.append(source_helper(source))
    return sources

@app.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str):
    source = await db["sources"].find_one({"_id": ObjectId(source_id)})
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source_helper(source)

@app.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source: Source):
    source = jsonable_encoder(source)
    result = await db["sources"].update_one({"_id": ObjectId(source_id)}, {"$set": source})
    if result.modified_count == 1:
        updated_source = await db["sources"].find_one({"_id": ObjectId(source_id)})
        return source_helper(updated_source)
    else:
        raise HTTPException(status_code=404, detail="Source not found")

@app.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str):
    result = await db["sources"].delete_one({"_id": ObjectId(source_id)})
    if result.deleted_count == 1:
        return
    else:
        raise HTTPException(status_code=404, detail="Source not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)