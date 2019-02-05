# -*- coding: utf-8 -*-
"""
A representation of a Locust Task.
"""

import json
from types import MappingProxyType
from typing import Iterable, NamedTuple, Iterator, Sequence, Optional, Mapping, List

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

    NOOP_HTTP_METHODS = {HttpMethod.GET, HttpMethod.OPTIONS, HttpMethod.DELETE}

    def as_locust_action(self) -> str:
        args = {
            "url": self.url,
            "name": self.url,
            "headers": self.headers,
            "timeout": TIMEOUT,
            "allow_redirects": False,
        }
        if self.method is HttpMethod.POST:
            post_data = _parse_post_data(self.post_data)
            args[post_data["key"]] = post_data["data"]
        elif self.method is HttpMethod.PUT:
            post_data = _parse_post_data(self.post_data)
            args["params"] = zip_kv_pairs(self.query)
            args[post_data["key"]] = post_data["data"]
        elif self.method not in self.NOOP_HTTP_METHODS:
            raise ValueError(f"unsupported HTTP method: {self.method!r}")

        method = self.method.name.lower()
        named_args = ", ".join(f"{k}={v}" for k, v in args.items())
        return f"response = self.client.{method}({named_args})"


class Task2:
    def __init__(
        self,
        name: str,
        request: Request,
        statements: Sequence[py.Statement] = (),
        # TODO: Replace me with a plugin framework that accesses the full tree.
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        global_code_blocks: Mapping[str, Sequence[str]] = IMMUTABLE_EMPTY_DICT,
    ) -> None:
        self.name = name
        self.request = request
        self.statements = list(statements)
        self.global_code_blocks = {k: list(v) for k, v in global_code_blocks.items()}

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
        #   contain the equivalent of LocustRequest.
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        for req in sorted(requests, key=lambda r: r.timestamp):
            if not on_blacklist(req.url.netloc):
                yield cls(name=req.task_name(), request=req, statements=...)

    @classmethod
    def from_task(cls, task: "Task") -> "Task2":
        # TODO: Remove me as soon as the old Task is no longer used and Task2 is
        #   renamed to Task.
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        locust_request = task.locust_request
        if locust_request is None:
            locust_request = LocustRequest.from_request(task.request)
        return cls(
            name=task.name,
            request=task.request,
            statements=[
                py.OpaqueBlock(block)
                for block in [
                    *task.locust_preprocessing,
                    locust_request.as_locust_action(),
                    *task.locust_postprocessing,
                ]
            ],
        )


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
