# -*- coding: utf-8 -*-
"""
A representation of a Locust Task.
"""

import json
from collections import OrderedDict
from types import MappingProxyType
from typing import (
    Iterable,
    NamedTuple,
    Iterator,
    Sequence,
    Optional,
    Mapping,
    List,
    Dict,
)

from dataclasses import dataclass

import transformer.python as py
from transformer.blacklist import on_blacklist
from transformer.helpers import zip_kv_pairs
from transformer.request import HttpMethod, Request, QueryPair

IMMUTABLE_EMPTY_DICT = MappingProxyType({})
TIMEOUT = 30
ACTION_INDENTATION_LEVEL = 12


class LocustRequest(NamedTuple):
    """
    All parameters for the request performed by the Locust client object.
    """

    method: HttpMethod
    url: str
    headers: Mapping[str, str]
    post_data: dict = MappingProxyType({})
    query: Sequence[QueryPair] = ()

    @classmethod
    def from_request(cls, r: Request) -> "LocustRequest":
        return LocustRequest(
            method=r.method,
            url=repr(r.url.geturl()),
            headers=zip_kv_pairs(r.headers),
            post_data=r.post_data,
            query=r.query,
        )


@dataclass
class Task2:
    name: str
    request: Request
    statements: Sequence[py.Statement] = ()
    # TODO: Replace me with a plugin framework that accesses the full tree.
    #   See https://github.com/zalando-incubator/Transformer/issues/11.
    global_code_blocks: Mapping[str, Sequence[str]] = IMMUTABLE_EMPTY_DICT

    def __post_init__(self,) -> None:
        self.statements = list(self.statements)
        self.global_code_blocks = {
            k: list(v) for k, v in self.global_code_blocks.items()
        }

    @classmethod
    def from_requests(cls, requests: Iterable[Request]) -> Iterator["Task2"]:
        """
        Generates a set of tasks from a given set of HTTP requests.
        Each request will be turned into an unevaluated function call making
        the actual request.
        The returned tasks are ordered by increasing timestamp of the
        corresponding request.
        """
        # TODO: Update me when merging Task with Task2: "statements" needs to
        #   contain a Placeholder to Task2.request.
        #   See what is done in from_task (but without the LocustRequest part).
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        for req in sorted(requests, key=lambda r: r.timestamp):
            if not on_blacklist(req.url.netloc):
                yield cls(name=req.task_name(), request=req, statements=...)

    @classmethod
    def from_task(cls, task: "Task") -> "Task2":
        # TODO: Remove me as soon as the old Task is no longer used and Task2 is
        #   renamed to Task.
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        t = cls(name=task.name, request=task.request)
        if task.locust_request:
            placeholder = py.Placeholder(
                name="this task's request field",
                target=lambda: task.locust_request,
                converter=lreq_to_expr,
            )
        else:
            placeholder = py.Placeholder(
                name="this task's request field",
                target=lambda: t.request,
                converter=req_to_expr,
            )
        t.statements = [
            *[py.OpaqueBlock(x) for x in task.locust_preprocessing],
            py.Assignment("response", placeholder),
            *[py.OpaqueBlock(x) for x in task.locust_postprocessing],
        ]
        return t


NOOP_HTTP_METHODS = {HttpMethod.GET, HttpMethod.OPTIONS, HttpMethod.DELETE}


def req_to_expr(r: Request) -> py.FunctionCall:
    url = py.Literal(str(r.url.geturl()))
    args: Dict[str, py.Expression] = OrderedDict(
        url=url,
        name=url,
        headers=py.Literal(zip_kv_pairs(r.headers)),
        timeout=py.Literal(TIMEOUT),
        allow_redirects=py.Symbol("False"),
    )
    if r.method is HttpMethod.POST:
        post_data = _parse_post_data(r.post_data)
        args[post_data["key"]] = post_data["data"]
    elif r.method is HttpMethod.PUT:
        post_data = _parse_post_data(r.post_data)
        args[post_data["key"]] = post_data["data"]
        args["params"] = zip_kv_pairs(r.query)
    elif r.method not in NOOP_HTTP_METHODS:
        raise ValueError(f"unsupported HTTP method: {r.method!r}")

    method = r.method.name.lower()
    return py.FunctionCall(name=f"self.client.{method}", named_args=args)


def lreq_to_expr(lr: LocustRequest) -> py.FunctionCall:
    # TODO: Remove me once LocustRequest no longer exists.
    #   See https://github.com/zalando-incubator/Transformer/issues/11.
    if lr.url.startswith("f"):
        url = py.FString(lr.url[2:-1])
    else:
        url = py.Literal(lr.url[1:-1])

    args: Dict[str, py.Expression] = OrderedDict(
        url=url,
        name=url,
        headers=py.Literal(lr.headers),
        timeout=py.Literal(TIMEOUT),
        allow_redirects=py.Symbol("False"),
    )
    if lr.method is HttpMethod.POST:
        post_data = _parse_post_data(lr.post_data)
        args[post_data["key"]] = post_data["data"]
    elif lr.method is HttpMethod.PUT:
        args["params"] = zip_kv_pairs(lr.query)
        post_data = _parse_post_data(lr.post_data)
        args[post_data["key"]] = post_data["data"]
    elif lr.method not in NOOP_HTTP_METHODS:
        raise ValueError(f"unsupported HTTP method: {lr.method!r}")

    method = lr.method.name.lower()
    return py.FunctionCall(name=f"self.client.{method}", named_args=args)


class Task(NamedTuple):
    """
    One step of "doing something" on a website.
    This basically represents a @task in Locust-speak.
    """

    name: str
    request: Request
    locust_request: Optional[LocustRequest] = None
    locust_preprocessing: Sequence[str] = ()
    locust_postprocessing: Sequence[str] = ()
    global_code_blocks: Mapping[str, Sequence[str]] = MappingProxyType({})

    @classmethod
    def from_requests(cls, requests: Iterable[Request]) -> Iterator["Task"]:
        """
        Generates a set of Tasks from a given set of Requests.
        """

        for req in sorted(requests, key=lambda r: r.timestamp):
            if on_blacklist(req.url.netloc):
                continue
            else:
                yield cls(name=req.task_name(), request=req)

    def as_locust_action(self, indentation=ACTION_INDENTATION_LEVEL) -> str:
        """
        Converts a Task into a Locust Action.
        """
        action: List[str] = []

        for preprocessing in self.locust_preprocessing:
            action.append(_indent(preprocessing, indentation))

        if self.locust_request is None:
            locust_request = LocustRequest.from_request(self.request)
        else:
            locust_request = self.locust_request

        action.append(locust_request.as_locust_action())

        for postprocessing in self.locust_postprocessing:
            action.append(_indent(postprocessing, indentation))

        return "\n".join(action)

    def inject_headers(self, headers: dict):
        if self.locust_request is None:
            original_locust_request = LocustRequest.from_request(self.request)
        else:
            original_locust_request = self.locust_request

        new_locust_request = original_locust_request._replace(
            headers={**original_locust_request.headers, **headers}
        )
        task = self._replace(locust_request=new_locust_request)

        return task

    def replace_url(self, url: str):
        if self.locust_request is None:
            original_locust_request = LocustRequest.from_request(self.request)
        else:
            original_locust_request = self.locust_request

        new_locust_request = original_locust_request._replace(url=url)
        return self._replace(locust_request=new_locust_request)


def _indent(input_string: str, requested_indentation: int) -> str:
    output_string = ""
    indentation = requested_indentation
    initial_leading_spaces = 0
    for i, line in enumerate(input_string.splitlines()):

        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:

            # We need to check the indentation of the second line in order to
            # account for the case where the existing indentation is greater than
            # the requested; it is used for reapplying sub-level-indentation e.g.
            # to if statements.
            if i == 1:
                initial_leading_spaces = leading_spaces
            else:
                indentation = requested_indentation + (
                    leading_spaces - initial_leading_spaces
                )

            line = line.lstrip()

        output_string += line.rjust(len(line) + indentation, " ") + "\n"

    return output_string


def _parse_post_data(post_data: dict) -> dict:
    data = post_data.get("text")
    mime: str = post_data.get("mimeType")
    if mime == "application/json":
        key = "json"
        # Workaround for bug in chrome-har:
        # https://github.com/sitespeedio/chrome-har/issues/23
        # TODO: Remove once bug fixed.
        if data is None:
            params = post_data.get("params")
            if params is None:
                data = ""
            else:
                data = {}
                for param in params:
                    data[param.get("name")] = param.get("value")
        else:
            data = json.loads(data)
    else:
        key = "data"
        if data:
            data = data.encode()
    return {"key": key, "data": data}
