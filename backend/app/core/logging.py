import sys
from loguru import logger


def setup_logging():
    """Configura el sistema de logging estructurado con loguru."""
    logger.remove()
    
    # Formato de consola para desarrollo y produccion
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format,
        level="DEBUG",
    )

    # Log persistente en archivo con rotacion
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="50 MB",
        retention="30 days",
        compression="zip",
        format=log_format,
        level="INFO",
    )


setup_logging()
