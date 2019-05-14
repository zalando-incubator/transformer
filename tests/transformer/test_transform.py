# pylint: skip-file
import io
from pathlib import Path

import pytest

import transformer
import transformer.transform as tt
from transformer.helpers import DUMMY_HAR_STRING
from transformer.locust import locustfile_lines
from transformer.plugins import plugin, Contract


class TestTransform:
    def test_it_returns_a_locustfile_program_given_scenario_path(self, tmp_path: Path):
        har_path = tmp_path / "some.har"
        har_path.write_text(DUMMY_HAR_STRING)
        locustfile_contents = str(tt.transform(har_path))
        try:
            compile(locustfile_contents, "locustfile.py", "exec")
        except Exception as exception:
            pytest.fail(f"Compiling locustfile failed. [{exception}].")

    def test_it_uses_default_plugins(self, tmp_path: Path, monkeypatch):
        har_path = tmp_path / "some.har"
        har_path.write_text(DUMMY_HAR_STRING)

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


def dump_as_str(*args, **kwargs):
    """
    Wraps transformer.dump by passing it a StringIO buffer as file argument and
    returning the final contents of that buffer.
    This makes transformer.dump behave like transformer.dumps, and thus allows
    to test their output more easily.
    """
    s = io.StringIO()
    transformer.dump(s, *args, **kwargs)
    return s.getvalue()


class TestDumpAndDumps:
    @pytest.mark.parametrize("f", (transformer.dumps, dump_as_str))
    def test_with_no_paths_it_returns_empty_locustfile(self, f):
        expected_empty_locustfile = "\n".join(
            locustfile_lines(scenarios=[], program_plugins=())
        )
        assert f([]) == expected_empty_locustfile

    def test_dump_and_dumps_have_same_output_for_simple_har(self, tmp_path):
        har_path = tmp_path / "some.har"
        har_path.write_text(DUMMY_HAR_STRING)

        assert transformer.dumps([tmp_path]) == dump_as_str([tmp_path])

    @pytest.mark.parametrize(
        "f,with_default,expected_times_called",
        (
            (f, *case)
            for f in (transformer.dumps, dump_as_str)
            for case in ((True, 1), (False, 0))
        ),
    )
    def test_it_uses_default_plugins(
        self, tmp_path: Path, monkeypatch, f, with_default, expected_times_called
    ):
        har_path = tmp_path / "some.har"
        har_path.write_text(DUMMY_HAR_STRING)

        times_plugin_called = 0

        @plugin(Contract.OnScenario)
        def fake_plugin(t):
            nonlocal times_plugin_called
            times_plugin_called += 1
            return t

        monkeypatch.setattr(tt, "DEFAULT_PLUGINS", [fake_plugin])

        f([har_path], with_default_plugins=with_default)

        assert times_plugin_called == expected_times_called
