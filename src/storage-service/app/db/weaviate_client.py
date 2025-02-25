import weaviate
import weaviate.classes.config as wvcc
import os

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
                wvcc.Property(name='Date', data_type=wvcc.DataType.TEXT, description="Publication date"), # If I use the DataType.DATE format, it expects a string with the date in a RFC 3339 timestamps
                wvcc.Property(name='Source', data_type=wvcc.DataType.TEXT, description="URL of the source"),
            ]
        )
    finally:
        client.close()
