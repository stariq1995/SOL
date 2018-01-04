# coding=utf-8
""" Contains various custom defined exceptions
"""


class SOLException(Exception):
    """ Base formulation exception class"""
    pass


class InvalidConfigException(SOLException):
    """ Formulation received an invalid configuration
    """
    pass


class NoPathsException(InvalidConfigException):
    """
    No paths present for a commodity
    """
    pass


class UnsupportedOperationException(Exception):
    """
    Something is either not allowed or not implemented yet
    """
    pass


class ControllerException(Exception):
    """
    Something went wrong with the SDN controller
    """
    pass


class CompositionException(SOLException):
    """
    Something went wrong during composition of multiple applications
    """
    pass
