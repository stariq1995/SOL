# coding: utf-8

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())
__all__ = ['logger']
