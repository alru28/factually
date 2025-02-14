from datetime import datetime, timedelta
from app.core.scrapper import scrape_articles_base, scrape_articles_content
from app.utils.storage import store_articles_to_json

def main():
    date_base = datetime.today().date()
    fecha_cutoff = date_base - timedelta(days=1)
    articulos = []
    articulos += scrape_articles_base('theregister', date_base, fecha_cutoff)
    articulos += scrape_articles_base('theverge', date_base, fecha_cutoff)
    articulos += scrape_articles_base('techcrunch', date_base, fecha_cutoff)
    articulos += scrape_articles_base('wired', date_base, fecha_cutoff)
    articulos += scrape_articles_base('arstechnica', date_base, fecha_cutoff)
    # articulos += scrape_articles_base('wsj', date_base, fecha_cutoff) # PAYWALL
    store_articles_to_json(articulos, filename=f"{date_base.strftime("%Y-%m-%d")}_01_links.json")
    articulos_contenido = scrape_articles_content(articulos)
    store_articles_to_json(articulos_contenido, filename=f"{date_base.strftime("%Y-%m-%d")}_02_noticias.json")

if __name__ == "__main__":
    main()