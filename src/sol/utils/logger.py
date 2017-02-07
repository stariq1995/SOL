# coding: utf-8

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler, StreamHandler

logger = logging.getLogger('sol')
logger.addHandler(NullHandler())
__all__ = ['logger']


def init_logger(level=logging.DEBUG):
    """
    Defuault logger initializer. Uses console output and sets level to DEBUG

    :param level custom logging level
    :return: the logger instance
    """
    logger.addHandler(StreamHandler())
    logger.setLevel(level)
    return logger
