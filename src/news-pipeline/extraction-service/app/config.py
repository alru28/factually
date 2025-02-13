# SOURCE DICTIONARY
sources = {
    'theverge': {
        'base_url': 'https://www.theverge.com',
        'url': 'https://www.theverge.com/archives/{year}/{month}/{page}',
        'article_selector': 'duet--content-cards--content-card _1ufh7nr1 _1ufh7nr0 _1lkmsmo0',
        'date_format': '%b %d',
        'button_selector': None,
    },
    'techcrunch': {
        'base_url': 'https://techcrunch.com',
        'url': 'https://techcrunch.com/{year}/{month}/page/{page}',
        'article_selector': 'loop-card loop-card--post-type-post loop-card--default loop-card--horizontal loop-card--wide loop-card--force-storyline-aspect-ratio',
        'date_format': '%b %d, %Y',
        'button_selector': None,
    },
    'wired': {
        'base_url': 'https://es.wired.com',
        'url': 'https://es.wired.com/tag/inteligencia-artificial?page={page}',
        'article_selector': 'summary-item__content',
        'date_format': '%d de %B de %Y',
        'button_selector': None,
    },
    'wsj': {
        'base_url': 'https://www.wsj.com',
        'url': 'https://www.wsj.com/news/archive/{year}/{month}/{day}?page={page}',
        'article_selector': 'WSJTheme--overflow-hidden--qJmlzHgO',
        'date_format': 'None',
        'button_selector': None,
    },
    'arstechnica': {
        'base_url': 'https://arstechnica.com',
        'url': 'https://arstechnica.com/{year}/page/{page}',
        'article_selector': 'flex flex-1 flex-col justify-between pl-3 sm:pl-5',
        'date_format': '%d/%m/%Y',
        'button_selector': 'post-navigation-link',
    },
    'xataka': {
        'base_url': 'https://www.xataka.com',
        'url': 'https://www.xataka.com/archivos/{year}/{month}',
        'article_selector': None,
        'date_format': '%d de %B de %Y',
        'button_selector': None,
    },
    'theregister': {
        'base_url': 'https://www.theregister.com',
        'url': 'https://www.theregister.com/Archive/{year}/{month}/{day}/',
        'article_selector': 'article_text_elements',
        'date_format': '%d %b, %Y',
        'button_selector': None,
    },
}