"""
:mod:`transformer` -- Main API
============================================

This module exports the functions that should cover most use-cases of any
Transformer user.
"""
from .transform import dumps, dump
from ._version import __version__ as package_version

__version__ = package_version

__all__ = ["dumps", "dump"]
