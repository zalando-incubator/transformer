from typing import Sequence, Callable

from transformer.task import Task

Plugin = Callable[[Sequence[Task]], Sequence[Task]]
