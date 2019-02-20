import logging
from typing import cast

from transformer.plugins import plugin, Contract
from transformer.request import Request
from transformer.scenario import Scenario
from transformer.task import Task


@plugin(Contract.OnScenario)
def f(s: Scenario) -> Scenario:
    first_req = first(s)
    logging.info(f"The first request was {first_req.url.geturl()}")
    return s


def first(s: Scenario) -> Request:
    while isinstance(s, Scenario):
        s = s.children[0]
    return cast(Task, s).request
