import json
from pytest import fixture


@fixture
def mock_open(mocker):
    return mocker.patch("builtins.open")


@fixture
def dummy_har_dict():
    return {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2018-01-01",
                    "request": {"method": "GET", "url": "https://www.zalando.de"},
                }
            ]
        }
    }


@fixture
def dummy_har_string(dummy_har_dict):
    return json.dumps(dummy_har_dict)


@fixture
def mocked_har(mocker, dummy_har_dict):
    j = mocker.patch("transformer.scenario.json.load")
    j.return_value = dummy_har_dict
    return j


@fixture
def mock_paths(mocker):
    mocker.patch("transformer.scenario.Path.is_dir").return_value = False
    mocker.patch("transformer.scenario.Path.iterdir").return_value = ()
    mocker.patch("transformer.scenario.Path.open")
