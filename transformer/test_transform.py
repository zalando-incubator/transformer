# pylint: skip-file
import json
from pathlib import Path

import pytest

import transformer.transform
from transformer.helpers import _DUMMY_HAR_DICT


class TestTransform:
    def test_it_returns_a_locustfile_string_given_scenario_path(self, tmp_path: Path):
        har_path = tmp_path / "some.har"
        with har_path.open("w") as file:
            json.dump(_DUMMY_HAR_DICT, file)
        locustfile_contents = str(transformer.transform.transform(har_path))
        try:
            compile(locustfile_contents, "locustfile.py", "exec")
        except Exception as exception:
            pytest.fail(f"Compiling locustfile failed. [{exception}].")
