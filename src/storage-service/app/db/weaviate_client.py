import os
from weaviate.connect import ConnectionParams
from weaviate import WeaviateAsyncClient
import weaviate.classes.config as wvcc
from typing import List
from app.utils.logger import DefaultLogger
from app.models import Article, article_to_weaviate_object

logger = DefaultLogger("StorageService").get_logger()

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
WEAVIATE_PORT = os.getenv("WEAVIATE_PORT", "8080")
OLLAMA_CONNECTION_STRING = os.getenv("OLLAMA_CONNECTION_STRING", "http://ollama:11434")
WEAVIATE_GRPC = os.getenv("WEAVIATE_GRPC", "50051")

class WeaviateAsyncClientSingleton:
    _client: WeaviateAsyncClient = None

    @classmethod
    async def init_client(cls) -> WeaviateAsyncClient:
        if cls._client is None:
            cls._client = WeaviateAsyncClient(
                connection_params=ConnectionParams.from_params(
                    http_host=WEAVIATE_HOST,
                    http_port=WEAVIATE_PORT,
                    http_secure=False,
                    grpc_host=WEAVIATE_HOST,
                    grpc_port=WEAVIATE_GRPC,
                    grpc_secure=False,
                )
            )
            await cls._client.connect()
            logger.info("Connected to Weaviate async instance")
        return cls._client

    @classmethod
    def get_client(cls) -> WeaviateAsyncClient:
        if cls._client is None:
            raise Exception("Weaviate async client not initialized")
        return cls._client

    @classmethod
    async def close_client(cls):
        if cls._client is not None:
            await cls._client.close()
            logger.info("Weaviate async client closed")
            cls._client = None
        else:
            raise Exception("Weaviate async client not initialized")

async def create_article_schema():
    client = WeaviateAsyncClientSingleton.get_client()
    try:
        await client.collections.create(
            name="Article",
            description="An article stored for hybrid search",
            vectorizer_config=[
                wvcc.Configure.NamedVectors.text2vec_ollama(
                    name="ContentVector",
                    source_properties=["content"],
                    api_endpoint=OLLAMA_CONNECTION_STRING,
                    model="nomic-embed-text"
                ),
            ],
            generative_config=wvcc.Configure.Generative.ollama(
                api_endpoint=OLLAMA_CONNECTION_STRING,
                model="llama3.2:1b"
            ),
            properties=[
                wvcc.Property(name='title', data_type=wvcc.DataType.TEXT, description="Title of the article"),
                wvcc.Property(name='content', data_type=wvcc.DataType.TEXT, description="Combined article content"),
                wvcc.Property(name='summary', data_type=wvcc.DataType.TEXT, description="Brief summary of the article"),
                wvcc.Property(name='sentiment', data_type=wvcc.DataType.TEXT, description="Sentiment analysis of the article"),
                wvcc.Property(name='classification', data_type=wvcc.DataType.TEXT, description="Classification labels for the article"),
                wvcc.Property(name='date', data_type=wvcc.DataType.TEXT, description="Publication date"),
                wvcc.Property(name='source', data_type=wvcc.DataType.TEXT, description="URL of the source"),
            ]
        )
        logger.info("Article collection schema created in Weaviate")
    except Exception as e:
        logger.error(f"Error creating article schema: {e}")
        raise e

async def sync_articles_to_weaviate(articles_list: List[Article]):
    client = WeaviateAsyncClientSingleton.get_client()
    articles_collection = client.collections.get("Article")

    for article_obj in articles_list:
        if isinstance(article_obj, dict):
                article_obj = Article.parse_obj(article_obj)
        obj = article_to_weaviate_object(article_obj)

        try:
            does_exist = await articles_collection.data.exists(article_obj.id)
            if does_exist:
                logger.debug(f"Article {article_obj.id} already exists in Weaviate during sync, trying to update.")
                await articles_collection.data.update(
                    uuid = article_obj.id,
                    properties = obj
                )
            else:
                logger.debug(f"Article {article_obj.id} doesn't exists in Weaviate during sync, trying to insert.")
                await articles_collection.data.insert(
                    uuid = article_obj.id,
                    properties = obj
                )
        except Exception as e:
            logger.error(f"Article {article_obj.id} couldn't be synced to Weaviate: {e}")

    logger.info(f"Synced {len(articles_list)} articles into Weaviate.")