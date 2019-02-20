import logging
import os
from pathlib import Path

import transformer
from transformer.helpers import DUMMY_HAR_STRING


def test_dummy_plugin_works(tmp_path: Path, caplog):
    har_path = tmp_path / "test.har"
    har_path.write_text(DUMMY_HAR_STRING)

    caplog.set_level(logging.INFO)

    with open(os.path.devnull, "w") as f:
        transformer.dump(f, [har_path], plugins=["transformer.plugins.dummy"])

    assert "The first request was https://www.zalando.de" in caplog.text
