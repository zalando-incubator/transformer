"""
This module defines the various kinds of plugins supported by Transformer.

Transformer plugins are just functions that accept certain inputs and have
certain outputs. Different kinds of plugins have different input and output
types. These input and output types are formalized here using Python's
annotation syntax and the typing module.
"""
from typing import Sequence, Callable

from transformer.task import Task

# Historically Transformer has only one kind of plugin, which transformed a
# sequence of Task objects into another such sequence. Operating on a full list
# of tasks (instead of task by task) offered more leeway: a plugin could e.g.
# add a new task, or change only the first task.
# However this OnTaskSequence model is too constraining for some use-cases,
# e.g. when a plugin needs to inject code in the global scope, and having to
# deal with a full, immutable list of tasks in plugins that independently
# operate on each task implies a lot of verbosity and redundancy.
# For these reasons, other plugin kinds were created to offer a more varied
# choice for plugin implementers.
# See https://github.com/zalando-incubator/Transformer/issues/10.
OnTaskSequence = Callable[[Sequence[Task]], Sequence[Task]]
