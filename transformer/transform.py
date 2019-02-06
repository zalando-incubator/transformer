# -*- coding: utf-8 -*-
"""
Entrypoint for Transformer.
"""
from pathlib import Path
from typing import Sequence, Union

import transformer.python as py
from transformer.locust import locustfile
from transformer.plugins import sanitize_headers
from transformer.plugins.contracts import OnTaskSequence
from transformer.scenario import Scenario

DEFAULT_PLUGINS = [sanitize_headers.plugin]


def transform(
    scenarios_path: Union[str, Path], plugins: Sequence[OnTaskSequence] = ()
) -> py.Program:
    actual_plugins = [*DEFAULT_PLUGINS, *plugins]
    return locustfile([Scenario.from_path(Path(scenarios_path), actual_plugins)])
