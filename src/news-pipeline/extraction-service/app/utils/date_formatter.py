import re
import locale
from datetime import datetime, timedelta
from app.utils.logger import DefaultLogger

def format_date_str(text_date: str, format: str) -> datetime.date:
    """
    Formats a text date string into a datetime.date object using the specified format.

    The function attempts to parse the given date string by first removing any leading words such as
    'updated', 'published' or blank space, then trying specific locales and common date formats. If relative date formats
    (e.g., '2 days ago') are detected, they are processed accordingly. In case of failure, a warning is logged
    and the current date is returned as a fallback.

    Args:
        text_date (str): The date string to be formatted.
        format (str): The expected date format for parsing the date string.

    Returns:
        datetime.date: The formatted date object.
    """
    # REMOVE UPTADED OR PUBLISHED OR BLANK STARTING TEXT
    text_date = re.sub(r'^(updated|published)\s+', '', text_date, flags=re.IGNORECASE).strip()
    
   # 1. TEST SPECIFIC FORMAT IN ENG/ESP
    for loc in ["en_US.UTF-8", "es_ES.UTF-8"]:
        try:
            locale.setlocale(locale.LC_TIME, loc)
            parsed_date = datetime.strptime(text_date, format).date()

            if parsed_date.year == 1900:
                parsed_date = parsed_date.replace(year=datetime.now().year)

            return parsed_date
        except (ValueError, locale.Error):
            continue
    
    # 2. TEST COMMON FORMATS
    formats_alternative = [
        "%d/%m/%Y",    # 22/1/2025
        "%m/%d/%Y",    # 1/22/2025
        "%d-%m-%Y",    # 22-1-2025
        "%m-%d-%Y",    # 1-22-2025
        "%Y-%m-%d",    # 2025-1-22
        "%Y/%m/%d",    # 2025/1/22
        "%d %b %Y",    # 22 Jan 2025
        "%d de %B de %Y",  # 22 de enero de 2025
        "%B %d, %Y",   # January 22, 2025
    ]
    
    for fmt in formats_alternative:
        try:
            return datetime.strptime(text_date, fmt).date()
        except ValueError:
            continue

    # 3. TEST RELATIVE FORMATS
    if any(keyword in text_date.lower() for keyword in ['ago', 'hace']):
        try:
            matches = None
            # ENG/ESP
            if 'ago' in text_date.lower():
                matches = re.search(r'(\d+)\s+(minute|hour|day)s?\s+ago', text_date, re.IGNORECASE)
            else:
                matches = re.search(r'hace\s+(\d+)\s+(minuto|hora|d[ií]a)s?', text_date, re.IGNORECASE)
            
            if matches:
                n = int(matches.group(1))
                unit = matches.group(2).lower().replace('í', 'i').replace('á', 'a')
                
                delta_mapping = {
                    'minute': timedelta(minutes=1),
                    'minuto': timedelta(minutes=1),
                    'hour': timedelta(hours=1),
                    'hora': timedelta(hours=1),
                    'day': timedelta(days=1),
                    'dia': timedelta(days=1)
                }
                
                if unit in delta_mapping:
                    delta = delta_mapping[unit] * n
                    return (datetime.now() - delta).date()
        
        except Exception as e:
            DefaultLogger().get_logger().error(f"Error processing relative date: {e}")

    # 4. FALLBACK
    DefaultLogger().get_logger().warning(f"Date not parsed: {text_date}. Format given {format}. Using fallback")
    return datetime.today().date()