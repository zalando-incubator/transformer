# pylint: skip-file

import io
import json
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib.parse import urlparse

import pytest

from transformer.request import Header
from transformer.task import (
    Task,
    Request,
    HttpMethod,
    QueryPair,
    TIMEOUT,
    LocustRequest,
)


class TestFromRequests:
    def test_it_returns_a_task(self):
        request = MagicMock()
        request.timestamp = 1
        second_request = MagicMock()
        second_request.timestamp = 2
        assert all(
            isinstance(t, Task) for t in Task.from_requests([request, second_request])
        )

    @patch("builtins.open")
    def test_it_doesnt_create_a_task_if_the_url_is_on_the_blacklist(self, mock_open):
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


class TestAsLocustAction:
    def test_it_returns_an_error_given_an_unsupported_http_method(self):
        a_request_with_an_unsupported_http_method = MagicMock()
        task = Task("some_task", a_request_with_an_unsupported_http_method)
        with pytest.raises(ValueError):
            task.as_locust_action()

    def test_it_returns_a_string(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        assert isinstance(task.as_locust_action(), str)

    def test_it_returns_action_from_locust_request(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        locust_request = LocustRequest(
            method=HttpMethod.GET, url=repr("http://locust-task"), headers={}
        )
        task = Task("some_task", request=a_request, locust_request=locust_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.get(url='http://locust-task'")

    def test_it_returns_task_using_get_given_a_get_http_method(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.get(")

    def test_it_returns_a_task_using_post_given_a_post_http_method(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.POST
        a_request.post_data = {}
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.post(")

    def test_it_returns_a_task_using_put_given_a_put_http_method(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.PUT
        a_request.post_data = {"text": "{'some key': 'some value'}"}
        a_request.query = [QueryPair(name="some name", value="some value")]
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.put(")
        assert "params={'some name': 'some value'}" in action
        assert "data=b\"{'some key': 'some value'}\"" in action

    def test_it_returns_a_task_using_options_given_an_options_http_method(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.OPTIONS
        a_request.headers = [Header(name="Access-Control-Request-Method", value="POST")]
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.options(")
        assert "headers={'Access-Control-Request-Method': 'POST'" in action

    def test_it_returns_a_task_using_delete_given_a_delete_http_method(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.DELETE
        a_request.url = urlparse("http://www.some.web.site/?some_name=some_value")
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert action.startswith("response = self.client.delete(")
        assert "?some_name=some_value" in action

    def test_it_provides_timeout_to_requests(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert f"timeout={TIMEOUT}" in action

    def test_it_injects_headers(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        a_request.headers = [Header(name="some_header", value="some_value")]
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert "some_value" in action

    def test_it_encodes_data_in_task_for_text_mime(self):
        decoded_value = '{"formatted": "54,95 €"}'
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.POST
        a_request.post_data = {"text": decoded_value}
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert str(decoded_value.encode()) in action

    def test_it_encodes_data_in_task_for_json_mime(self):
        decoded_value = '{"formatted": "54,95 €"}'
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.POST
        a_request.post_data = {"text": decoded_value, "mimeType": "application/json"}
        task = Task("some_task", a_request)
        action = task.as_locust_action()
        assert str(json.loads(decoded_value)) in action

    def test_it_converts_post_params_to_post_text(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.POST
        a_request.post_data = {
            "mimeType": "application/json",
            "params": [
                {"name": "username", "value": "some user"},
                {"name": "password", "value": "some password"},
            ],
        }
        task = Task("some task", a_request)
        action = task.as_locust_action()
        assert "'username': 'some user'" in action
        assert "'password': 'some password'" in action

    def test_it_creates_a_locust_request_when_there_is_none(self):
        task = Task(name="some name", request=MagicMock())

        modified_task = Task.inject_headers(task, {})

        assert modified_task.locust_request

    def test_it_returns_a_task_with_the_injected_headers(self):
        locust_request = LocustRequest(
            method=MagicMock(), url=MagicMock(), headers={"x-forwarded-for": ""}
        )
        task = Task(
            name="some name", request=MagicMock(), locust_request=locust_request
        )
        expected_headers = {"x-forwarded-for": "1.2.3.4"}
        modified_task = Task.inject_headers(task, headers=expected_headers)

        assert isinstance(modified_task, Task)

        headers = modified_task.locust_request.headers
        assert len(headers) == 1
        assert headers == expected_headers


class TestIndentation:
    def test_pre_processing_returns_an_indented_string_given_an_indentation(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        new_pre_processings = (*task.locust_preprocessing, "def some_function():")
        task = task._replace(locust_preprocessing=new_pre_processings)
        action = task.as_locust_action(indentation=2)
        assert action.startswith("  def some_function():")

    def test_post_processing_returns_an_indented_string_given_an_indentation(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        new_post_processings = (*task.locust_postprocessing, "def some_function():")
        task = task._replace(locust_postprocessing=new_post_processings)
        action = task.as_locust_action(indentation=2)
        assert "  def some_function():" in action

    def test_it_applies_indentation_to_all_pre_processings(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        new_pre_processings = (
            *task.locust_preprocessing,
            "def some_function():",
            "def some_other_function():",
        )
        task = task._replace(locust_preprocessing=new_pre_processings)
        action = task.as_locust_action(indentation=2)
        assert action.startswith(
            "  def some_function():\n\n  def some_other_function():"
        )

    def test_it_respects_sub_indentation_levels(self):
        a_request = MagicMock(spec_set=Request)
        a_request.method = HttpMethod.GET
        task = Task("some_task", a_request)
        new_pre_processings = (
            *task.locust_preprocessing,
            "\n  def function():\n   if True:\n    print(True)",
        )
        task = task._replace(locust_preprocessing=new_pre_processings)
        action = task.as_locust_action(indentation=1)
        assert action.startswith(" \n def function():\n  if True:\n   print(True)")


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
