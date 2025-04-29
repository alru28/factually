from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.db.mongo import db
from app.db.weaviate_client import create_article_schema, WeaviateAsyncClientSingleton
from app.api.routes import router
import requests
import uvicorn
import os
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
    logger.info("Startup event: Initializing Weaviate and Article schema")
    await WeaviateAsyncClientSingleton.init_client()
    await create_article_schema()    
    
    # App running
    yield

    logger.info("Shutdown event: Closing Weaviate async client")
    await WeaviateAsyncClientSingleton.close_client()

app = FastAPI(lifespan=lifespan, title="Storage Service", openapi_url="/openapi.json")
app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting Storage Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
