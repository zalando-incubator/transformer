# pylint: skip-file
from unittest.mock import MagicMock
from transformer.task import Task, LocustRequest
from transformer.request import HttpMethod, Header
from .sanitize_headers import plugin


def test_it_removes_headers_beginning_with_a_colon():
    tasks = [
        Task(
            name="some task",
            request=None,
            locust_request=LocustRequest(
                method=HttpMethod.GET,
                url="",
                headers=[Header(name=":non-rfc-header", value="some value")],
            ),
        )
    ]
    sanitized_headers = plugin(tasks)[0].locust_request.headers
    assert len(sanitized_headers) == 0


def test_it_downcases_header_names():
    tasks = [
        Task(
            name="some task",
            request=None,
            locust_request=LocustRequest(
                method=HttpMethod.GET,
                url="",
                headers=[Header(name="Some Name", value="some value")],
            ),
        )
    ]
    sanitized_headers = plugin(tasks)[0].locust_request.headers
    assert "some name" in sanitized_headers


def test_it_removes_cookies():
    tasks = [
        Task(
            name="someTask",
            request=None,
            locust_request=LocustRequest(
                method=HttpMethod.GET,
                url="",
                headers=[Header(name="cookie", value="some value")],
            ),
        )
    ]
    sanitized_headers = plugin(tasks)[0].locust_request.headers
    assert len(sanitized_headers) == 0


def test_it_does_not_remove_other_headers():
    tasks = [
        Task(
            name="someTask",
            request=None,
            locust_request=LocustRequest(
                method=HttpMethod.GET,
                url="",
                headers=[Header(name="some other header", value="some value")],
            ),
        )
    ]
    sanitized_headers = plugin(tasks)[0].locust_request.headers
    assert len(sanitized_headers) == 1


def test_it_creates_a_locust_request_if_none_exist():
    tasks = [Task(name="some task", request=MagicMock())]
    assert plugin(tasks)[0].locust_request
