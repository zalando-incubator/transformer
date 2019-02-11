# -*- coding: utf-8 -*-
"""
Entrypoint for Transformer.
"""
from pathlib import Path
from typing import Sequence, Union

import transformer.python as py
from transformer.locust import locustfile
from transformer.plugins.contracts import OnTaskSequence
from transformer.scenario import Scenario


def transform(
    scenarios_path: Union[str, Path], plugins: Sequence[OnTaskSequence] = ()
) -> py.Program:
    return locustfile([Scenario.from_path(Path(scenarios_path), plugins)])
