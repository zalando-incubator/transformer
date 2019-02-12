# pylint: skip-file
import json
from pathlib import Path

import pytest

import transformer.transform as tt
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

    def test_it_uses_default_plugins(self, tmp_path: Path, monkeypatch):
        har_path = tmp_path / "some.har"
        with har_path.open("w") as file:
            json.dump(_DUMMY_HAR_DICT, file)

        times_plugin_called = 0

        # We don't need to specify a plugin signature here because signatures
        # are only checked at plugin name resolution.
        def fake_plugin(tasks):
            nonlocal times_plugin_called
            times_plugin_called += 1
            return tasks

        monkeypatch.setattr(tt, "DEFAULT_PLUGINS", [fake_plugin])

        tt.transform(har_path, plugins=[])  # explicitly provide no plugins

        assert times_plugin_called == 1
