from transformer.plugins import plugin, Contract
from transformer.request import Header
from transformer.task import Task2


@plugin(Contract.OnTask)
def plugin(task: Task2) -> Task2:
    """
    Removes Chrome-specific, RFC-non-compliant headers starting with `:`.
    Converts header names to lowercase to simplify further overriding.
    Removes the cookie header as it is handled by Locust's HttpSession.
    """
    sanitized_headers = [
        Header(name=h.name.lower(), value=h.value)
        for h in task.request.headers
        if not h.name.startswith(":") and h.name.lower() != "cookie"
    ]

    task.request = task.request._replace(headers=sanitized_headers)

    return task
