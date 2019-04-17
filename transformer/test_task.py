# pylint: skip-file
import enum
import io
from unittest.mock import MagicMock, Mock
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from hypothesis import given
from hypothesis.strategies import composite, sampled_from, booleans

from transformer import python as py
from transformer.request import Header, QueryPair
from transformer.task import (
    Task,
    Request,
    HttpMethod,
    TIMEOUT,
    LocustRequest,
    Task2,
    RequestsPostData,
    JSON_MIME_TYPE,
    req_to_expr,
    lreq_to_expr,
)


class TestTask:
    class TestFromRequests:
        def test_it_returns_a_task(self):
            request = MagicMock()
            request.timestamp = 1
            second_request = MagicMock()
            second_request.timestamp = 2
            assert all(
                isinstance(t, Task)
                for t in Task.from_requests([request, second_request])
            )

        @patch("builtins.open")
        def test_it_doesnt_create_a_task_if_the_url_is_on_the_blacklist(
            self, mock_open
        ):
            mock_open.return_value = io.StringIO("amazon")
            request = MagicMock()
            request.url = MagicMock()
            request.url.netloc = "www.amazon.com"
            task = Task.from_requests([request])
            assert len(list(task)) == 0

        @patch("builtins.open")
        def test_it_creates_a_task_if_the_path_not_host_is_on_the_blacklist(
            self, mock_open
        ):
            mock_open.return_value = io.StringIO("search\namazon")
            request = MagicMock()
            request.url = urlparse("https://www.google.com/search?&q=amazon")
            task = Task.from_requests([request])
            assert len(list(task)) == 1

    class TestReplaceURL:
        def test_it_creates_a_locust_request_when_there_is_none(self):
            task = Task(name="some name", request=MagicMock())

            modified_task = Task.replace_url(task, "")

            assert modified_task.locust_request

        def test_it_returns_a_task_with_the_replaced_url(self):
            locust_request = LocustRequest(
                method=MagicMock(), url=MagicMock(), headers=MagicMock()
            )
            task = Task(
                name="some name", request=MagicMock(), locust_request=locust_request
            )
            expected_url = 'f"http://a.b.c/{some.value}/"'

            modified_task = Task.replace_url(task, expected_url)

            assert modified_task.locust_request.url == expected_url


class TestTask2:
    class TestFromTask:
        def test_without_locust_request_it_proxies_the_request(self):
            req = Mock(spec_set=Request)
            task = Task(name="T", request=req)
            task2 = Task2.from_task(task)

            assert task2.name == "T"
            assert task2.request == req
            assert len(task2.statements) == 1

            assign = task2.statements[0]
            assert isinstance(assign, py.Assignment)
            assert assign.lhs == "response"

            assert isinstance(assign.rhs, py.ExpressionView)
            assert assign.rhs.target() == task2.request
            assert assign.rhs.converter is req_to_expr

        def test_with_locust_request_it_proxies_it(self):
            lr = Mock(spec_set=LocustRequest)
            req = Mock(spec_set=Request)
            task = Task(name="T", request=req, locust_request=lr)
            task2 = Task2.from_task(task)

            assert task2.name == "T"
            assert task2.request == req
            assert len(task2.statements) == 1

            assign = task2.statements[0]
            assert isinstance(assign, py.Assignment)
            assert assign.lhs == "response"

            assert isinstance(assign.rhs, py.ExpressionView)
            assert assign.rhs.target() == lr
            assert assign.rhs.converter is lreq_to_expr


class _KindOfDict(enum.Flag):
    Text = enum.auto()
    Params = enum.auto()
    Both = Text | Params


_formats = sampled_from(("json", "www"))
_kinds_of_dicts = sampled_from(_KindOfDict)


# From http://www.softwareishard.com/blog/har-12-spec/#postData.
@composite
def har_post_dicts(draw, format=None):
    format = format or draw(_formats)
    if format == "json":
        d = {"mimeType": "application/json", "text": """{"a":"b", "c": "d"}"""}
        if draw(booleans()):
            d["params"] = []
        if draw(booleans()):
            d["comment"] = ""
        return d

    d = {"mimeType": "application/x-www-form-urlencoded"}
    kind = draw(_kinds_of_dicts)
    if kind & _KindOfDict.Text:
        d["text"] = "a=b&c=d"
        if draw(booleans()):
            d.setdefault("params", [])
    if kind & _KindOfDict.Params:
        d["params"] = [{"name": "a", "value": "b"}, {"name": "c", "value": "d"}]
        if draw(booleans()):
            d.setdefault("text", "")
    return d


class TestRequestPostData:
    def test_as_kwargs_only_shows_defined(self):
        v, w = MagicMock(), MagicMock()
        assert RequestsPostData(data=v).as_kwargs() == {"data": v}
        assert RequestsPostData(params=v, json=w).as_kwargs() == {
            "params": v,
            "json": w,
        }

    class TestFromHarPostData:
        @given(har_post_dicts(format="json"))
        def test_it_selects_json_approach_for_json_format(self, d: dict):
            rpd = RequestsPostData.from_har_post_data(d)
            assert rpd.json == py.Literal({"a": "b", "c": "d"})
            assert rpd.data is None

        @given(har_post_dicts(format="www"))
        def test_it_selects_data_approach_for_urlencoded_format(self, d: dict):
            rpd = RequestsPostData.from_har_post_data(d)
            assert rpd.json is None
            assert rpd.data == py.Literal(b"a=b&c=d") or rpd.params == py.Literal(
                [(b"a", b"b"), (b"c", b"d")]
            )

        @given(har_post_dicts())
        def test_it_doesnt_raise_error_on_valid_input(self, d: dict):
            RequestsPostData.from_har_post_data(d)

        def test_it_raises_on_post_data_without_text_or_params(self):
            with pytest.raises(ValueError):
                RequestsPostData.from_har_post_data({"mimeType": "nil"})

        def test_it_raises_on_invalid_json(self):
            with pytest.raises(ValueError):
                RequestsPostData.from_har_post_data(
                    {"mimeType": JSON_MIME_TYPE, "text": "not json"}
                )

        @pytest.mark.parametrize(
            "mime,kwarg,val",
            (
                (JSON_MIME_TYPE, "json", {}),
                ("application/x-www-form-urlencoded", "data", b"{}"),
            ),
        )
        def test_it_accepts_both_params_and_text(self, mime: str, kwarg, val):
            expected_fields = {
                "params": py.Literal([(b"n", b"v")]),
                kwarg: py.Literal(val),
            }
            assert RequestsPostData.from_har_post_data(
                {
                    "mimeType": mime,
                    "text": "{}",
                    "params": [{"name": "n", "value": "v"}],
                }
            ) == RequestsPostData(**expected_fields)


class TestReqToExpr:
    def test_it_supports_get_requests(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.GET,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            query=[QueryPair("x", "y")],  # query is currently ignored for GET
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.get",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )

    def test_it_supports_urlencoded_post_requests(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.POST,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            post_data={
                "mimeType": "application/x-www-form-urlencoded",
                "params": [{"name": "x", "value": "y"}],
                "text": "z=7",
            },
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "data": py.Literal(b"z=7"),
                "params": py.Literal([(b"x", b"y")]),
            },
        )

    def test_it_supports_json_post_requests(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.POST,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            post_data={
                "mimeType": "application/json",
                "params": [{"name": "x", "value": "y"}],
                "text": """{"z": 7}""",
            },
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "json": py.Literal({"z": 7}),
                "params": py.Literal([(b"x", b"y")]),
            },
        )

    def test_it_supports_empty_post_requests(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.POST,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            post_data=None,
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )

    def test_it_supports_put_requests_with_payload(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.PUT,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            query=[QueryPair("c", "d")],
            post_data={
                "mimeType": "application/json",
                "params": [{"name": "x", "value": "y"}],
                "text": """{"z": 7}""",
            },
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.put",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "json": py.Literal({"z": 7}),
                "params": py.Literal([(b"x", b"y"), (b"c", b"d")]),
            },
        )

    def test_it_supports_put_requests_without_payload(self):
        url = "http://abc.de"
        r = Request(
            timestamp=MagicMock(),
            method=HttpMethod.PUT,
            url=urlparse(url),
            har_entry={"entry": "data"},
            headers=[Header("a", "b")],
            query=[QueryPair("c", "d")],
            post_data=None,
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.put",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "params": py.Literal([(b"c", b"d")]),
            },
        )

    def test_it_uses_the_custom_name_if_provided(self):
        url = "http://abc.de"
        name = "my-req"
        r = Request(
            name=name, timestamp=MagicMock(), method=HttpMethod.GET, url=urlparse(url), har_entry={"entry": "data"}
        )
        assert req_to_expr(r) == py.FunctionCall(
            name="self.client.get",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(name),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )


class TestLreqToExpr:
    def test_it_supports_get_requests(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.GET,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                query=[QueryPair("x", "y")],  # query is currently ignored for GET
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.get",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )

    def test_it_supports_fstring_urls(self):
        url = "http://abc.{tld}"
        r = LocustRequest(method=HttpMethod.GET, url=f"f'{url}'", headers={"a": "b"})
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.get",
            named_args={
                "url": py.FString(url),
                "name": py.FString(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )

    def test_it_supports_urlencoded_post_requests(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.POST,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                post_data={
                    "mimeType": "application/x-www-form-urlencoded",
                    "params": [{"name": "x", "value": "y"}],
                    "text": "z=7",
                },
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "data": py.Literal(b"z=7"),
                "params": py.Literal([(b"x", b"y")]),
            },
        )

    def test_it_supports_json_post_requests(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.POST,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                post_data={
                    "mimeType": "application/json",
                    "params": [{"name": "x", "value": "y"}],
                    "text": """{"z": 7}""",
                },
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "json": py.Literal({"z": 7}),
                "params": py.Literal([(b"x", b"y")]),
            },
        )

    def test_it_supports_empty_post_requests(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.POST,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                post_data=None,
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.post",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )

    def test_it_supports_put_requests_with_payload(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.PUT,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                query=[QueryPair("c", "d")],
                post_data={
                    "mimeType": "application/json",
                    "params": [{"name": "x", "value": "y"}],
                    "text": """{"z": 7}""",
                },
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.put",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "json": py.Literal({"z": 7}),
                "params": py.Literal([(b"x", b"y"), (b"c", b"d")]),
            },
        )

    def test_it_supports_put_requests_without_payload(self):
        url = "http://abc.de"
        r = LocustRequest.from_request(
            Request(
                timestamp=MagicMock(),
                method=HttpMethod.PUT,
                url=urlparse(url),
                har_entry={"entry": "data"},
                headers=[Header("a", "b")],
                query=[QueryPair("c", "d")],
                post_data=None,
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.put",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(url),
                "headers": py.Literal({"a": "b"}),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
                "params": py.Literal([(b"c", b"d")]),
            },
        )

    def test_it_uses_the_custom_name_if_provided(self):
        url = "http://abc.de"
        name = "my-req"
        r = LocustRequest.from_request(
            Request(
                name=name,
                timestamp=MagicMock(),
                method=HttpMethod.GET,
                url=urlparse(url),
                har_entry={"entry": "data"}
            )
        )
        assert lreq_to_expr(r) == py.FunctionCall(
            name="self.client.get",
            named_args={
                "url": py.Literal(url),
                "name": py.Literal(name),
                "timeout": py.Literal(TIMEOUT),
                "allow_redirects": py.Literal(False),
            },
        )
