from app.models import ArticleBase, Article
from typing import List
from app.utils.logger import DefaultLogger
import json
import csv

def str_encoder(obj):
    try:
        return str(obj)
    except Exception:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def store_articles_to_json(articles: List[Article], filename="articles.json"):
    articles_dict = [article.model_dump() for article in articles]
    
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(articles_dict, json_file, default=str_encoder, ensure_ascii=False, indent=4)
    
    DefaultLogger().get_logger().info(f"Stored {len(articles)} articles in {filename}")