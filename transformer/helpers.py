import json


"""
Use this with caution, as it is global and mutable!
See also DUMMY_HAR_STRING.
"""
_DUMMY_HAR_DICT = {
    "log": {
        "entries": [
            {
                "startedDateTime": "2018-01-01",
                "request": {"method": "GET", "url": "https://www.zalando.de"},
            }
        ]
    }
}

DUMMY_HAR_STRING = json.dumps(_DUMMY_HAR_DICT)
