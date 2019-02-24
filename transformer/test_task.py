# pylint: skip-file

import io
import json
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

from transformer.request import Header
from transformer import python as py
from transformer.task import (
    Task,
    Request,
    HttpMethod,
    QueryPair,
    TIMEOUT,
    LocustRequest,
    Task2,
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
        def test_without_locust_request(self):
            url = "https://abc.de"
            req = Request(
                timestamp=datetime.now(),
                method=HttpMethod.GET,
                url=urlparse(url),
                headers=[Header("a", "b")],
                post_data={},
                query=[],
            )
            task = Task(name="T", request=req)
            task2 = Task2.from_task(task)

            assert task2.name == "T"
            assert task2.request == req
            assert len(task2.statements) == 1

            assign = task2.statements[0]
            assert isinstance(assign, py.Assignment)
            assert assign.lhs == "response"

            assert isinstance(assign.rhs, py.Placeholder)
            assert assign.rhs.target() == task2.request

            assert str(assign.rhs) == (
                f"self.client.get(url={url!r}, name={url!r},"
                f" headers={{'a': 'b'}}, timeout={TIMEOUT}, allow_redirects=False)"
            )

        def test_with_locust_request(self):
            url = "https://abc.de"
            req = Request(
                timestamp=datetime.now(),
                method=HttpMethod.GET,
                url=urlparse(url),
                headers=[Header("a", "b")],
                post_data={},
                query=[],
            )
            lr = LocustRequest.from_request(req)
            lr = lr._replace(url="f" + lr.url.replace("de", "{tld}"))
            task = Task(name="T", request=req, locust_request=lr)
            task2 = Task2.from_task(task)

            assert task2.name == "T"
            assert task2.request == req
            assert len(task2.statements) == 1

            assign = task2.statements[0]
            assert isinstance(assign, py.Assignment)
            assert assign.lhs == "response"

            assert isinstance(assign.rhs, py.Placeholder)
            assert assign.rhs.target() == lr

            expected_url = """ f'https://abc.{tld}' """.strip()
            assert str(assign.rhs) == (
                f"self.client.get(url={expected_url}, name={expected_url},"
                f" headers={{'a': 'b'}}, timeout={TIMEOUT}, allow_redirects=False)"
            )
