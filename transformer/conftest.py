import json

import pytest


@pytest.fixture
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


@pytest.fixture
def dummy_har_string():
    return json.dumps(dummy_har_dict())
