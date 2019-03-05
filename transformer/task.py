"""
:mod:`transformer.task` -- HTTP requests and related processing
===============================================================

Each HTTP request from a HAR file is seen by Transformer as a separate
:term:`task` to be eventually converted into a :any:`locust.core.task` function:

.. figure:: _static/basic-conversion.*
   :align: center

   *Transformer converts HAR requests into Locust tasks.*

:class:`~transformer.request.Request` only represents an HTTP request, not the
potential pre- and post-processing that could be desired in the same Locust task
(e.g. before or after the ``requests.get`` call).
Transformer's :term:`task` is an object encapsulating a
:class:`~transformer.request.Request` *and* that additional processing code,
in a one-to-one relationship with :any:`locust.core.task`-decorated functions.

However, Transformer's tasks have no notion of :ref:`weight <specifying-weights>`
or :ref:`grouping <hierarchical-scenarios>`: these come with
:term:`scenarios <scenario>`.
"""
import json
from collections import OrderedDict
from json import JSONDecodeError
from types import MappingProxyType
from typing import (
    Iterable,
    NamedTuple,
    Iterator,
    Sequence,
    Optional,
    Mapping,
    Dict,
    List,
    Tuple,
    cast,
)

import dataclasses
from dataclasses import dataclass

import transformer.python as py
from transformer.blacklist import on_blacklist
from transformer.helpers import zip_kv_pairs
from transformer.request import HttpMethod, Request, QueryPair

IMMUTABLE_EMPTY_DICT = MappingProxyType({})
TIMEOUT = 30
ACTION_INDENTATION_LEVEL = 12
JSON_MIME_TYPE = "application/json"


class LocustRequest(NamedTuple):
    """
    All parameters for the request performed by the Locust client object.

    .. deprecated:: 1.0.2
        Only used by :class:`Task`, which is itself deprecated.
        Use :class:`Task2` instead of :class:`Task`.
    """

    method: HttpMethod
    url: str
    headers: Mapping[str, str]
    post_data: dict = MappingProxyType({})
    query: Sequence[QueryPair] = ()
    name: Optional[str] = None

    @classmethod
    def from_request(cls, r: Request) -> "LocustRequest":
        return LocustRequest(
            method=r.method,
            url=repr(r.url.geturl()),
            headers=zip_kv_pairs(r.headers),
            post_data=r.post_data,
            query=r.query,
            name=repr(r.name or r.url.geturl()),
        )


@dataclass
class Task2:
    """
    Represents a :term:`task`, i.e. an HTTP request along with some optional
    pre- and post-processing code.

    .. attribute:: name

        :any:`str` --
        Name of the corresponding :any:`locust.core.task` function in
        the locustfile.

    .. attribute:: request

        :any:`transformer.request.Request` --
        HTTP request executed by this task.

    .. attribute:: statements

        :any:`Sequence <typing.Sequence>` of |Statement| --
        Body of the corresponding :any:`locust.core.task` function in the
        locustfile.

        One of these statements contains an |ExpressionView| pointing to
        :attr:`request`.
        The other statements (if any) represent pre- or post-processing code
        for that request, depending on whether they appear before or after the
        statement containing the |ExpressionView|.

        .. warning::

            Plugins should be careful if they replace the |ExpressionView|
            object found in :attr:`statements`.
            Other plugins should still be able to change :attr:`request` and
            expect to see these changes reflected in :attr:`statements` via
            |ExpressionView|.

    .. attribute:: global_code_blocks

        :any:`Mapping <typing.Mapping>` of
        :any:`str` to |Statement|

        .. deprecated:: 1.0.2

            This attribute is only kept for backward compatibility purposes.
            It exists because Transformer's first plugin system didn't have
            :term:`OnPythonProgram`, so plugins had to specify the top-level
            locustfile code blocks they needed (e.g. imports, global variables)
            at the :class:`Task` level and let the plugin system percolate these
            code blocks through the scenario tree.
            This explains why scenarios have the similar
            :any:`transformer.scenario.Scenario.global_code_blocks` field.
    """

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

        Each request will be turned into an unevaluated function call
        (:class:`transformer.python.FunctionCall`)
        making the actual request.

        The returned tasks are ordered by increasing :any:`timestamp
        <transformer.request.Request.timestamp>` of the corresponding request.
        """
        # TODO: Update me when merging Task with Task2: "statements" needs to
        #   contain a ExpressionView to Task2.request.
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
            expr_view = py.ExpressionView(
                name="this task's request field",
                target=lambda: task.locust_request,
                converter=lreq_to_expr,
            )
        else:
            expr_view = py.ExpressionView(
                name="this task's request field",
                target=lambda: t.request,
                converter=req_to_expr,
            )
        t.statements = [
            *[py.OpaqueBlock(x) for x in task.locust_preprocessing],
            py.Assignment("response", expr_view),
            *[py.OpaqueBlock(x) for x in task.locust_postprocessing],
        ]
        return t


NOOP_HTTP_METHODS = {HttpMethod.GET, HttpMethod.OPTIONS, HttpMethod.DELETE}


def req_to_expr(r: Request) -> py.FunctionCall:
    url = py.Literal(str(r.url.geturl()))
    headers = zip_kv_pairs(r.headers)
    args: Dict[str, py.Expression] = OrderedDict(
        url=url,
        name=py.Literal(r.name) if r.name else url,
        timeout=py.Literal(TIMEOUT),
        allow_redirects=py.Literal(False),
    )
    if headers:
        args["headers"] = py.Literal(headers)

    if r.method is HttpMethod.POST:
        if r.post_data:
            rpd = RequestsPostData.from_har_post_data(r.post_data)
            args.update(rpd.as_kwargs())
    elif r.method is HttpMethod.PUT:
        if r.post_data:
            rpd = RequestsPostData.from_har_post_data(r.post_data)
            args.update(rpd.as_kwargs())

        args.setdefault("params", py.Literal([]))
        cast(py.Literal, args["params"]).value.extend(
            _params_from_name_value_dicts([dataclasses.asdict(q) for q in r.query])
        )
    elif r.method not in NOOP_HTTP_METHODS:
        raise ValueError(f"unsupported HTTP method: {r.method!r}")

    method = r.method.name.lower()
    return py.FunctionCall(name=f"self.client.{method}", named_args=args)


def lreq_to_expr(lr: LocustRequest) -> py.FunctionCall:
    # TODO: Remove me once LocustRequest no longer exists.
    #   See https://github.com/zalando-incubator/Transformer/issues/11.
    url = _peel_off_repr(lr.url)
    name = _peel_off_repr(lr.name) if lr.name else url

    args: Dict[str, py.Expression] = OrderedDict(
        url=url,
        name=name,
        timeout=py.Literal(TIMEOUT),
        allow_redirects=py.Literal(False),
    )
    if lr.headers:
        args["headers"] = py.Literal(lr.headers)

    if lr.method is HttpMethod.POST:
        if lr.post_data:
            rpd = RequestsPostData.from_har_post_data(lr.post_data)
            args.update(rpd.as_kwargs())
    elif lr.method is HttpMethod.PUT:
        if lr.post_data:
            rpd = RequestsPostData.from_har_post_data(lr.post_data)
            args.update(rpd.as_kwargs())

        args.setdefault("params", py.Literal([]))
        cast(py.Literal, args["params"]).value.extend(
            _params_from_name_value_dicts([dataclasses.asdict(q) for q in lr.query])
        )
    elif lr.method not in NOOP_HTTP_METHODS:
        raise ValueError(f"unsupported HTTP method: {lr.method!r}")

    method = lr.method.name.lower()
    return py.FunctionCall(name=f"self.client.{method}", named_args=args)


def _peel_off_repr(s: str) -> py.Literal:
    """
    Reverse the effect of LocustRequest's repr() calls on url and name.
    """
    if s.startswith("f"):
        return py.FString(eval(s[1:], {}, {}))
    return py.Literal(eval(s, {}, {}))


class Task(NamedTuple):
    """
    One step of "doing something" on a website.
    This basically represents a @task in Locust-speak.

    .. deprecated:: 1.0.2
        Use :class:`Task2` instead. :class:`Task` is kept for backward
        compatibility with existing plugins that have not yet migrated to
        :class:`Task2`.
        Transformer will automatically convert :class:`Task` objects into
        :class:`Task2` objects using :meth:`Task2.from_task`.
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


@dataclass
class RequestsPostData:
    """
    Data to be sent via HTTP POST, along with which API of the requests library
    to use.
    """

    data: Optional[py.Literal] = None
    params: Optional[py.Literal] = None
    json: Optional[py.Literal] = None

    def as_kwargs(self) -> Dict[str, py.Expression]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}

    @classmethod
    def from_har_post_data(cls, post_data: dict) -> "RequestsPostData":
        """
        Converts a HAR postData object into a RequestsPostData instance.

        :param post_data: a HAR "postData" object,
            see http://www.softwareishard.com/blog/har-12-spec/#postData.
        :raise ValueError: if *post_data* is invalid.
        """
        try:
            return _from_har_post_data(post_data)
        except ValueError as err:
            raise ValueError(f"invalid HAR postData object: {post_data!r}") from err


def _from_har_post_data(post_data: dict) -> RequestsPostData:
    mime_k = "mimeType"
    try:
        mime: str = post_data[mime_k]
    except KeyError:
        raise ValueError(f"missing {mime_k!r} field") from None

    rpd = RequestsPostData()

    # The "text" and "params" fields are supposed to be mutually
    # exclusive (according to the HAR spec) but nobody respects that.
    # Often, both text and params are provided for x-www-form-urlencoded.
    text_k, params_k = "text", "params"
    if text_k not in post_data and params_k not in post_data:
        raise ValueError(f"should contain {text_k!r} or {params_k!r}")

    _extract_text(mime, post_data, text_k, rpd)

    try:
        params = _params_from_post_data(params_k, post_data)
        if params is not None:
            rpd.params = py.Literal(params)
    except (KeyError, UnicodeEncodeError, TypeError) as err:
        raise ValueError("unreadable params field") from err

    return rpd


def _extract_text(
    mime: str, post_data: dict, text_k: str, rpd: RequestsPostData
) -> None:
    text = post_data.get(text_k)
    if mime == JSON_MIME_TYPE:
        if text is None:
            raise ValueError(f"missing {text_k!r} field for {JSON_MIME_TYPE} content")
        try:
            rpd.json = py.Literal(json.loads(text))
        except JSONDecodeError as err:
            raise ValueError(f"unreadable JSON from field {text_k!r}") from err
    elif text is not None:  # Probably application/x-www-form-urlencoded.
        try:
            rpd.data = py.Literal(text.encode())
        except UnicodeEncodeError as err:
            raise ValueError(f"cannot encode the {text_k!r} field in UTF-8") from err


def _params_from_post_data(
    key: str, post_data: dict
) -> Optional[List[Tuple[bytes, bytes]]]:
    """
    Extracts the *key* list from *post_data* and calls
    _params_from_name_value_dicts with that list.

    :raise TypeError: if the object at *key* is built using unexpected data types.
    """
    params = post_data.get(key)
    if params is None:
        return None
    if not isinstance(params, list):
        raise TypeError(f"the {key!r} field should be a list")
    return _params_from_name_value_dicts(params)


def _params_from_name_value_dicts(
    dicts: Iterable[Mapping[str, str]]
) -> List[Tuple[bytes, bytes]]:
    """
    Converts a HAR "params" element [0] into a list of tuples that can be used
    as value for requests' "params" keyword-argument.

    [0]: http://www.softwareishard.com/blog/har-12-spec/#params
    [1]: http://docs.python-requests.org/en/master/user/quickstart/
        #more-complicated-post-requests

    :raise KeyError: if one of the elements doesn't contain a "name" or "value" field.
    :raise UnicodeEncodeError: if an element's "name" or "value" string cannot
        be encoded in UTF-8.
    """
    return [(d["name"].encode(), d["value"].encode()) for d in dicts]
