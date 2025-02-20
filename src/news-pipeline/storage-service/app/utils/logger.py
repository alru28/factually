import logging
import sys

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Configures and returns a logger with the specified name and logging level.

    The logger is configured to write log messages to the console with a specified format.

    Args:
        name (str): The name of the logger.
        level (int, optional): The logging level. Default is logging.DEBUG.

    Returns:
        logging.Logger: The configured logger instance.
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
    Singleton class providing a default logger instance.

    This class ensures that only one logger instance is created and shared across the application.
    """
    def __new__(cls, name: str = "StorageService", level: int = logging.DEBUG):
        """
        Creates a new instance of DefaultLogger if one does not exist, otherwise returns the existing instance.

        Args:
            name (str, optional): The name of the logger. Default is "ExtractionService".
            level (int, optional): The logging level. Default is logging.DEBUG.

        Returns:
            DefaultLogger: The singleton instance of DefaultLogger.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(DefaultLogger, cls).__new__(cls)
            cls.instance.logger = setup_logger(name, level)
        return cls.instance

    def get_logger(self) -> logging.Logger:
        """
        Retrieves the logger instance.

        Returns:
            logging.Logger: The logger instance configured for the application.
        """
        return self.logger