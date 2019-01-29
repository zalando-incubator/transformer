from typing import Sequence

from transformer.task import Task, LocustRequest
from transformer.helpers import zip_kv_pairs


def plugin(tasks: Sequence[Task]) -> Sequence[Task]:
    """
    Removes Chrome-specific, RFC non-compliant headers starting with ":".
    Maps header keys to lowercase to make overriding deterministic.
    Removes cookie header as it is handled by Locust's HttpSession.
    """
    modified_tasks = []
    for task in tasks:

        if task.locust_request is None:
            task = task._replace(
                locust_request=LocustRequest.from_request(task.request)
            )

        headers = task.locust_request.headers

        if not isinstance(headers, dict):
            headers = zip_kv_pairs(headers)

        sanitized_headers = {
            k.lower(): v
            for (k, v) in headers.items()
            if not k.startswith(":") and k.lower() != "cookie"
        }

        task = task._replace(
            locust_request=task.locust_request._replace(headers=sanitized_headers)
        )

        modified_tasks.append(task)

    return modified_tasks
