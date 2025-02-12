from urllib.parse import urljoin

class SafeDict(dict):
    def __missing__(self, key):
        return f"{{{key}}}"

def safe_url_format(template: str, **kwargs) -> str:
    return template.format_map(SafeDict(**kwargs))

def fix_links(url_base: str, url_relative: str) -> str:
    if not url_relative.startswith(('http', 'www')):
        return urljoin(url_base, url_relative)
    return url_relative