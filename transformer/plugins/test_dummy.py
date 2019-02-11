import logging
from pathlib import Path

from transformer.helpers import DUMMY_HAR_STRING
from transformer.scenario import Scenario


def test_dummy_plugin_works(tmp_path: Path, caplog):
    from transformer.plugins import dummy

    har_path = tmp_path / "test.har"
    har_path.write_text(DUMMY_HAR_STRING)

    caplog.set_level(logging.INFO)

    Scenario.from_path(har_path, plugins=[dummy.plugin])

    assert "https://www.zalando.de" in caplog.text
