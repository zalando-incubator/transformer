from transformer.helpers import zip_kv_pairs
from transformer.plugins import plugin, Contract
from transformer.task import Task2


@plugin(Contract.OnTask)
def plugin(task: Task2) -> Task2:
    """
    Removes Chrome-specific, RFC-non-compliant headers starting with `:`.
    Converts header names to lowercase to simplify further overriding.
    Removes the cookie header as it is handled by Locust's HttpSession.
    """
    headers = task.request.headers

    if not isinstance(headers, dict):
        headers = zip_kv_pairs(headers)

    sanitized_headers = {
        k.lower(): v
        for (k, v) in headers.items()
        if not k.startswith(":") and k.lower() != "cookie"
    }

    task.request = task.request._replace(headers=sanitized_headers)

    return task
