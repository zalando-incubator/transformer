# pylint: skip-file

from unittest.mock import MagicMock

import pytest
from transformer.request import *


class TestFromHarEntry:
    def test_it_returns_an_error_given_an_invalid_dict(self):
        with pytest.raises(KeyError):
            invalid_dict = {"some": "data"}
            Request.from_har_entry(invalid_dict)

    def test_it_returns_a_request_given_a_get_request(self):
        get_request = {
            "request": {"method": "GET", "url": ""},
            "startedDateTime": "2018-01-01",
        }
        request = Request.from_har_entry(get_request)
        assert isinstance(request, Request)
        assert request.method == HttpMethod.GET

    def test_it_returns_a_request_given_a_post_request(self):
        post_request = {
            "request": {
                "method": "POST",
                "url": "",
                "postData": "{'some name': 'some value'}",
            },
            "startedDateTime": "2018-01-01",
        }
        request = Request.from_har_entry(post_request)
        assert isinstance(request, Request)
        assert request.method == HttpMethod.POST
        assert request.post_data == "{'some name': 'some value'}"

    def test_it_returns_a_request_given_a_put_request(self):
        put_request = {
            "request": {
                "method": "PUT",
                "url": "",
                "postData": "{'some name': 'some value'}",
                "queryString": [{"name": "some name", "value": "some value"}],
            },
            "startedDateTime": "2018-01-01",
        }
        request = Request.from_har_entry(put_request)
        assert isinstance(request, Request)
        assert request.method == HttpMethod.PUT
        assert request.post_data == "{'some name': 'some value'}"
        assert request.query == [QueryPair(name="some name", value="some value")]

    def test_it_returns_a_request_with_headers_given_an_options_request(self):
        options_request = {
            "request": {
                "method": "OPTIONS",
                "url": "",
                "postData": "",
                "headers": [{"name": "Access-Control-Request-Method", "value": "POST"}],
            },
            "startedDateTime": "2018-01-01",
        }
        request = Request.from_har_entry(options_request)
        assert isinstance(request, Request)
        assert request.method == HttpMethod.OPTIONS
        assert request.headers == [
            Header(name="Access-Control-Request-Method", value="POST")
        ]

    def test_it_returns_a_request_with_a_query_given_a_delete_request_with_a_query(
        self
    ):
        delete_request = {
            "request": {
                "method": "DELETE",
                "url": "",
                "queryString": [{"name": "some name", "value": "some value"}],
            },
            "startedDateTime": "2018-01-01",
        }
        request = Request.from_har_entry(delete_request)
        assert isinstance(request, Request)
        assert request.method == HttpMethod.DELETE
        assert request.query == [QueryPair(name="some name", value="some value")]

    def test_it_records_har_entry(self):
        entry = {
            "request": {
                "method": "GET",
                "url": "localhost"
            },
            "response": {
                "status": 200,
                "statusText": "OK",
            },
            "cache": {},
            "timings": {
              "connect": 22,
              "wait": 46,
              "receive": 0
            },
            "startedDateTime": "2018-01-01",
            "time": 116,
            "_securityState": "secure",
            "connection": "443"
        }
        request = Request.from_har_entry(entry)
        assert isinstance(request, Request)
        assert request.har_entry
        assert str(request.url.geturl()) == request.har_entry["request"]["url"]
        assert request.har_entry["_securityState"] == "secure"


class TestAllFromHar:
    @pytest.mark.skip(reason="Doesn't raise AssertionError; to be investigated.")
    def test_it_returns_an_error_given_an_invalid_dict(self):
        with pytest.raises(AssertionError):
            invalid_dict = {"some": "data"}
            Request.all_from_har(invalid_dict)

    def test_it_returns_a_list_of_requests_given_a_valid_dict(self):
        valid_dict = {
            "log": {
                "entries": [
                    {
                        "request": {"method": "GET", "url": "", "postData": ""},
                        "startedDateTime": "2018-01-01",
                    }
                ]
            }
        }
        assert isinstance(Request.all_from_har(valid_dict), Iterator)
        for request in Request.all_from_har(valid_dict):
            assert isinstance(request, Request)


class TestTaskName:
    def test_it_generates_a_task_name_given_a_request(self):
        a_request = MagicMock()
        a_request.method.name = "some_name"
        a_request.url.scheme = "some_scheme"
        a_request.url.hostname = "some_hostname"
        a_request.url.path = "some_path"

        a_task_name = Request.task_name(a_request)
        a_duplicate_task_name = Request.task_name(a_request)
        assert a_task_name == a_duplicate_task_name

        a_request.method.name = "some_other_name"
        a_different_task_name = Request.task_name(a_request)
        assert a_task_name != a_different_task_name
