import logging
import sys

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Configures and returns a logger with the specified name and logging level.
    This logger writes log messages to the console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        formatter = logging.Formatter(
            '[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

class DefaultLogger(object):
    """
    Singleton class with a default logger instance.
    """
    def __new__(cls, name: str = "StorageService", level: int = logging.DEBUG):
        # Only create one instance of DefaultLogger.
        if not hasattr(cls, 'instance'):
            cls.instance = super(DefaultLogger, cls).__new__(cls)
            cls.instance.logger = setup_logger(name, level)
        return cls.instance

    def get_logger(self) -> logging.Logger:
        return self.logger