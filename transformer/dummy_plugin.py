import logging
from typing import Sequence

from transformer.task import Task


def plugin(tasks: Sequence[Task]) -> Sequence[Task]:
    logging.info(f"The first request was {tasks[0].request.url.geturl()}")
    return tasks
