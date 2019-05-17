import logging
import os
from pathlib import Path

import transformer


def test_dummy_plugin_works(tmp_path: Path, caplog, dummy_har_string):
    har_path = tmp_path / "test.har"
    har_path.write_text(dummy_har_string)

    caplog.set_level(logging.INFO)

    with open(os.path.devnull, "w") as f:
        transformer.dump(f, [har_path], plugins=["transformer.plugins.dummy"])

    assert "The first request was https://www.zalando.de" in caplog.text
