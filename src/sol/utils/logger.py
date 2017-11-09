# coding: utf-8

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import StreamHandler, Formatter

logger = logging.getLogger('sol')
_been_initialized = False
__all__ = ['logger', 'init_logger']


def init_logger(level=logging.DEBUG):
    """
    Default logger initializer. Uses console output and sets level to DEBUG

    :param level custom logging level
    :return: the logger instance
    """
    # global _been_initialized
    # if not _been_initialized:
    #     s = StreamHandler()
    #     s.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    #     logger.addHandler(s)
    #     logger.setLevel(level)
    #     _been_initialized = True
    #     return logger
    # else:
    return logger
