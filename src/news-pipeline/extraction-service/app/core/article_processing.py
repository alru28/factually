from app.models import ArticleBase
from app.utils.url_helpers import fix_links
from app.utils.date_formatter import format_date_str
from app.utils.logger import DefaultLogger
import re

def process_articles_base(article_soup, source, date_base, date_cutoff) -> tuple[list[ArticleBase], bool]:
    valid_articles = []
    older_than_cutoff = False
    
    for article in article_soup:
        title_elem = article.find('h2') or article.find('h3') or article.find('h4') or article.find('a')
        date_elem = article.find('time')
        link_elem = (title_elem.find('a') if title_elem else None) or article.find('a') or article.parent

        # IF NO LINK - SKIP ARTICLE
        if not link_elem or not link_elem.get('href'):
            DefaultLogger().get_logger().warning(f"No link found in article from source {source['base_url']}")
            continue
        else:
            link = fix_links(source['base_url'], link_elem.get('href'))

        # IF NO DATE -> DATE = 'NoDate'
        if not date_elem:
            if '{day}' in source['url']:
                match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', link)
                if match:
                    year_extracted, month_extracted, day_extracted = match.groups()
                    date_text = f"{day_extracted}/{month_extracted}/{year_extracted}"
                    DefaultLogger().get_logger().debug(f"Date extracted from article URL: {date_text}")
                else:
                    DefaultLogger().get_logger().warning("Date couldn't be extracted from URL")
                    date_text = "NoDate"
            else:
                    DefaultLogger().get_logger().warning("Date couldn't be found in the article")
                    date_text = "NoDate"
        else:
            date_text = date_elem.get_text(strip=True) or date_elem.today().isoformat()

        # IF NO TITLE -> TITLE = 'NoTitle'
        if not title_elem:
            DefaultLogger().get_logger().warning("Title couldn't be found in the article")
            title = "NoTitle"
        else:
            title = title_elem.get_text(strip=True)

        try:
            date_article = format_date_str(date_text, source['date_format'])
        except Exception as e:
            DefaultLogger().get_logger().error("Error formatting date", exc_info=True)
            continue

        if date_article > date_base:
            DefaultLogger().get_logger().debug("Article date is newer than base date")
            continue
            
        if date_article < date_cutoff:
            DefaultLogger().get_logger().debug("Article date is older than cutoff date")
            older_than_cutoff = True
            break

        valid_articles.append(ArticleBase(
            Title=title,
            Date=date_article,
            Link=link
        ))
    
    return valid_articles, older_than_cutoff