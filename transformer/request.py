# -*- coding: utf-8 -*-
"""
A representation of a HAR Request.
"""

import enum
from datetime import datetime
from typing import Iterator, NamedTuple, List
from urllib.parse import urlparse, SplitResult

import pendulum

from transformer.naming import to_identifier


class HttpMethod(enum.Enum):
    """
    Enumeration of HTTP method types.
    """

    GET = enum.auto()
    POST = enum.auto()
    PUT = enum.auto()
    OPTIONS = enum.auto()
    DELETE = enum.auto()


class Header(NamedTuple):
    """
    HTTP header as recorded in HAR file.
    """

    name: str
    value: str


class QueryPair(NamedTuple):
    """
    Query String as recorded in HAR file.
    """

    name: str
    value: str


class Request(NamedTuple):
    """
    An HTTP request as recorded in a HAR file.
    """

    timestamp: datetime
    method: HttpMethod
    url: SplitResult
    headers: List[Header]
    post_data: dict
    query: List[QueryPair]

    @classmethod
    def from_har_entry(cls, entry: dict) -> "Request":
        """
        Creates a request from a HAR entry.
        """

        request = entry["request"]
        return Request(
            timestamp=pendulum.parse(entry["startedDateTime"]),
            method=HttpMethod[request["method"]],
            url=urlparse(request["url"]),
            headers=[
                Header(name=d["name"], value=d["value"])
                for d in request.get("headers", [])
            ],
            post_data=request.get("postData", {}),
            query=[
                QueryPair(name=d["name"], value=d["value"])
                for d in request.get("queryString", [])
            ],
        )

    @classmethod
    def all_from_har(cls, har: dict) -> Iterator["Request"]:
        """
        Generates requests for all entries in a given HAR file.
        """

        for entry in har["log"]["entries"]:
            yield cls.from_har_entry(entry)

    def task_name(self) -> str:
        """
        Generates a simple name suitable for use as a Python function.
        """

        return "_".join(
            (
                self.method.name,
                self.url.scheme,
                to_identifier(self.url.hostname),
                to_identifier(self.url.path),
                str(abs(hash(self))),
            )
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.timestamp,
                self.method,
                self.url,
                tuple(self.post_data) if self.post_data else None,
            )
        )
