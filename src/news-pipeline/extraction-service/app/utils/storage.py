from app.models import ArticleBase, Article
from typing import List
from app.utils.logger import DefaultLogger
import json
import csv


def str_encoder(obj):
    """
    Encodes an object into a string.

    This function attempts to convert the given object to a string. If the conversion fails,
    a TypeError is raised indicating that the object is not JSON serializable.

    Args:
        obj: The object to encode.

    Returns:
        str: The string representation of the object.

    Raises:
        TypeError: If the object cannot be converted to a string.
    """
    try:
        return str(obj)
    except Exception:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def store_articles_to_json(articles: List[Article], filename="articles.json"):
    """
    Stores a list of articles into a JSON file.

    The function serializes the list of Article objects into JSON format and writes it to the specified file.
    Logs an informational message upon successful storage.

    Args:
        articles (List[Article]): A list of Article objects to store.
        filename (str, optional): The filename to store the articles in. Default is "articles.json".
    """
    articles_dict = [article.model_dump() for article in articles]

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(
            articles_dict, json_file, default=str_encoder, ensure_ascii=False, indent=4
        )

    DefaultLogger().get_logger().info(f"Stored {len(articles)} articles in {filename}")
