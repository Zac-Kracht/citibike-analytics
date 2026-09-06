import logging
import sys


def get_logger(name: str = "citibike_etl", level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a standard Python logger for Glue ETL jobs and local execution.
    
    Args:
        name: The name of the logger (defaults to module/package name).
        level: Logging level threshold (defaults to INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger