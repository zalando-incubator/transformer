"""
This module defines the various kinds of plugins supported by Transformer.

Transformer plugins are just functions that accept certain inputs and have
certain outputs. Different kinds of plugins have different input and output
types. These input and output types are formalized here using Python's
annotation syntax and the typing module.
"""
from typing import Sequence, Callable

from transformer.task import Task

Plugin = Callable[[Sequence[Task]], Sequence[Task]]
