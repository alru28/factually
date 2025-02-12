from app.models import ArticleBase
from typing import List
from app.utils.logger import DefaultLogger
import json
import csv

def store_articles_to_json(articles: List[ArticleBase], filename="articles.json"):
    articles_dict = [article.model_dump_json() for article in articles]
    
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(articles_dict, json_file, ensure_ascii=False, indent=4)

    campos = list(articles[0].model_dump().keys())
    
    csv_filename = filename.replace(".json", ".csv")

    with open(csv_filename, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=campos)
        writer.writeheader()
        
        for article in articles:
            writer.writerow(article.model_dump())
    
    DefaultLogger().get_logger().info(f"Stored {len(articles)} articles in {filename}")