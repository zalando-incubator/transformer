from transformer.plugins import plugin, Contract
from transformer.task import Task2
from transformer.request import CaseInsensitiveDict

COOKIE_KEY = "cookie"


@plugin(Contract.OnTask)
def plugin(task: Task2) -> Task2:
    """
    Removes Chrome-specific, RFC-non-compliant headers starting with `:`.
    Removes the cookie header as it is handled by Locust's HttpSession.
    """
    task.request.headers = CaseInsensitiveDict(
        {k: v for k, v in task.request.headers.items() if not k.startswith(":")}
    )
    if COOKIE_KEY in task.request.headers:
        task.request.headers.pop(COOKIE_KEY)

    return task
