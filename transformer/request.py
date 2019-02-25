# -*- coding: utf-8 -*-
"""
A representation of a HAR Request.
"""

import enum
from datetime import datetime
from typing import Iterator, NamedTuple, List, Optional
from urllib.parse import urlparse, SplitResult

import pendulum
from dataclasses import dataclass

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


@dataclass
class QueryPair:
    """
    Query String as recorded in HAR file.
    """

    name: str
    value: str


@dataclass
class Request:
    """
    An HTTP request as recorded in a HAR file.

    Note that *post_data*, if present, will be a dict of the same format as read
    in the HAR file.
    Although not consistently followed by HAR generators, his format is
    documented here: http://www.softwareishard.com/blog/har-12-spec/#postData.
    """

    timestamp: datetime
    method: HttpMethod
    url: SplitResult
    headers: List[Header] = ()
    post_data: Optional[dict] = None
    query: List[QueryPair] = ()

    def __post_init__(self):
        self.headers = list(self.headers)
        self.query = list(self.query)

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
                tuple(self.post_data.items()) if self.post_data else None,
            )
        )
