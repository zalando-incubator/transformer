"""
:mod:`transformer.request` -- HTTP requests read from HAR
=========================================================

Representation of HAR Request objects.
"""

import enum
from datetime import datetime
from typing import Iterator, List, Optional
from urllib.parse import urlparse, SplitResult

import pendulum
from dataclasses import dataclass

from transformer.naming import to_identifier


class HttpMethod(enum.Enum):
    """
    Enumeration of supported HTTP method types.
    """

    GET = enum.auto()  #: GET
    POST = enum.auto()  #: POST
    PUT = enum.auto()  #: PUT
    OPTIONS = enum.auto()  #: OPTIONS
    DELETE = enum.auto()  #: DELETE


@dataclass(frozen=True)
class Header:
    """
    An HTTP header, as recorded in a HAR file (headers__).

    __ http://www.softwareishard.com/blog/har-12-spec/#headers
    """

    name: str
    value: str


@dataclass(frozen=True)
class QueryPair:
    """
    A pair of query parameters, as recorded in a HAR file (queryString__).

    __ http://www.softwareishard.com/blog/har-12-spec/#queryString
    """

    name: str
    value: str


@dataclass
class Request:
    """
    An HTTP request, as recorded in a HAR file (request__).

    __ http://www.softwareishard.com/blog/har-12-spec/#request

    Note that *post_data*, if present, will be a dict of the same format
    as recorded in the HAR file
    (postData__ -- although it is not consistently followed by HAR generators).

    __ http://www.softwareishard.com/blog/har-12-spec/#postData

    .. attribute:: timestamp

        :class:`~datetime.datetime` --
        Time at which the request was recorded.

    .. attribute:: method

        :class:`HttpMethod` --
        HTTP method of the request.

    .. attribute:: url

        :class:`urllib.parse.SplitResult` --
        URL targeted by the request.

    .. attribute:: har_entry

        :any:`dict` --
        A single record from entries as recorded in a HAR file
        (http://www.softwareishard.com/blog/har-12-spec/#entries)
        corresponding to the request, provided for read-only access.

    .. attribute:: headers
       :annotation: = []

       :class:`~typing.List` of :class:`Header` --
       HTTP headers sent with the request.

    .. attribute:: post_data
       :annotation: = None

       :data:`~typing.Optional` :any:`dict` --
       If :attr:`method` is ``POST``, the corresponding data payload.

    .. attribute:: query
       :annotation: = []

       :class:`~typing.List` of :class:`QueryPair` --
       Key-value arguments sent as part of the :attr:`url`'s `query string`__.

       __ https://en.wikipedia.org/wiki/Query_string

    .. attribute:: name
       :annotation: = None

       :data:`~typing.Optional` :any:`str` --
       Value provided for :class:`locust.clients.HttpSession`'s "dynamic"
       ``name`` parameter.
       See `Grouping requests to URLs with dynamic parameters`__ for details.

       __ https://docs.locust.io/en/stable/writing-a-locustfile.html
          #grouping-requests-to-urls-with-dynamic-parameters
    """

    timestamp: datetime
    method: HttpMethod
    url: SplitResult
    har_entry: dict
    headers: List[Header] = ()
    post_data: Optional[dict] = None
    query: List[QueryPair] = ()
    name: Optional[str] = None

    def __post_init__(self):
        self.headers = list(self.headers)
        self.query = list(self.query)

    @classmethod
    def from_har_entry(cls, entry: dict) -> "Request":
        """
        Creates a request from a HAR entry__.

        __ http://www.softwareishard.com/blog/har-12-spec/#entries

        :raise KeyError: if *entry* is not a valid HAR "entry" object.
        :raise ValueError: if the ``request.startedDateTime`` value cannot be
            interpreted as a timestamp.
        """

        request = entry["request"]
        return Request(
            timestamp=pendulum.parse(entry["startedDateTime"]),
            method=HttpMethod[request["method"]],
            url=urlparse(request["url"]),
            har_entry=entry,
            name=None,
            headers=[
                Header(name=d["name"], value=d["value"])
                for d in request.get("headers", [])
            ],
            post_data=request.get("postData"),
            query=[
                QueryPair(name=d["name"], value=d["value"])
                for d in request.get("queryString", [])
            ],
        )

    @classmethod
    def all_from_har(cls, har: dict) -> Iterator["Request"]:
        """
        Generates requests for all entries__ in a given HAR top-level object.

        __ http://www.softwareishard.com/blog/har-12-spec/#entries
        """

        for entry in har["log"]["entries"]:
            yield cls.from_har_entry(entry)

    def task_name(self) -> str:
        """
        Generates a simple name to be used as
        :attr:`~transformer.task.Task2.name` by the :term:`task` of this request.
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
                tuple(self.headers),
                repr(self.post_data) if self.post_data else None,
                tuple(self.query),
            )
        )
