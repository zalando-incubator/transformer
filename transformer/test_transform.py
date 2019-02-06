# pylint: skip-file
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import transformer.transform as tt
from transformer.transform import DEFAULT_PLUGINS
from transformer.helpers import _DUMMY_HAR_DICT


class TestTransform:
    def test_it_returns_a_locustfile_program_given_scenario_path(self, tmp_path: Path):
        har_path = tmp_path / "some.har"
        with har_path.open("w") as file:
            json.dump(_DUMMY_HAR_DICT, file)
        locustfile_contents = str(tt.transform(har_path))
        try:
            compile(locustfile_contents, "locustfile.py", "exec")
        except Exception as exception:
            pytest.fail(f"Compiling locustfile failed. [{exception}].")

    @patch("transformer.transform.locustfile")
    @patch("transformer.transform.Scenario.from_path")
    def test_it_uses_default_plugins(self, scenario_from_path, _, tmp_path: Path):
        har_path = tmp_path / "some.har"
        with har_path.open("w") as file:
            json.dump(_DUMMY_HAR_DICT, file)

        tt.transform(har_path)
        scenario_from_path.assert_called_once_with(har_path, DEFAULT_PLUGINS)
