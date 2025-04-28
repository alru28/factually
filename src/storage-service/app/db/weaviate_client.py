import weaviate
import weaviate.classes.config as wvcc
import os
from typing import List
from app.utils.logger import DefaultLogger
from app.models import Article, article_to_weaviate_object

logger = DefaultLogger("StorageService").get_logger()

WEAVIATE_HOST = os.getenv(
    "WEAVIATE_HOST", "http://weaviate"
)
WEAVIATE_PORT = os.getenv(
    "WEAVIATE_PORT", "8080"
)
OLLAMA_CONNECTION_STRING = os.getenv(
    "OLLAMA_CONNECTION_STRING", "http://ollama:11434"
)
WEAVIATE_GRPC = os.getenv(
    "WEAVIATE_GRPC", "50051"
)

def get_weaviate_client():
    client = weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT,
        grpc_port=WEAVIATE_GRPC,
    )
    print(client.is_ready())
    return client

def create_article_schema():
    client = get_weaviate_client()
    try:
        collection = client.collections.get("Article")
        logger.info("Article collection is already initialized in Weaviate")
    except:
        try:
            article_collection = client.collections.create(
                name="Article",
                description="An article stored for semantic/keyword search",
                vectorizer_config=wvcc.Configure.Vectorizer.text2vec_ollama(
                    api_endpoint=OLLAMA_CONNECTION_STRING,
                    model="nomic-embed-text"
                ),
                generative_config=wvcc.Configure.Generative.ollama(
                    api_endpoint=OLLAMA_CONNECTION_STRING,
                    model="llama3.2:1b"
                ),
                properties=[
                    wvcc.Property(name='Title', data_type=wvcc.DataType.TEXT, description="Title of the article"),
                    wvcc.Property(name='Content', data_type=wvcc.DataType.TEXT, description="Combined article content"),
                    wvcc.Property(name='Summary', data_type=wvcc.DataType.TEXT, description="Brief summary of the article"),
                    wvcc.Property(name='Sentiment', data_type=wvcc.DataType.TEXT, description="Sentiment analysis of the article"),
                    wvcc.Property(name='Classification', data_type=wvcc.DataType.TEXT, description="Classification labels for the article"),
                    wvcc.Property(name='Date', data_type=wvcc.DataType.TEXT, description="Publication date"), # If I use the DataType.DATE format, it expects a string with the date in a RFC 3339 timestamps
                    wvcc.Property(name='Source', data_type=wvcc.DataType.TEXT, description="URL of the source"),
                ]
            )
        finally:
            client.close()
    finally:
        client.close()
    

def sync_articles_to_weaviate(articles_list: List[Article]):
    client = get_weaviate_client()
    articles_collection = client.collections.get("Article")
    try:
        with articles_collection.batch.dynamic() as batch:
            for article_obj in articles_list:
                if isinstance(article_obj, dict):
                    article_obj = Article.parse_obj(article_obj)
                obj = article_to_weaviate_object(article_obj)
                batch.add_object(obj, uuid=article_obj.id)
        logger.info(f"Batch inserted {len(articles_list)} articles into Weaviate.")
    finally:
        client.close()