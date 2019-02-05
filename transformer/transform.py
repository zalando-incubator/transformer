# -*- coding: utf-8 -*-
"""
Entrypoint for Transformer.
"""
from pathlib import Path
from typing import Sequence, Union

import transformer.python as py
from transformer.locust import locustfile
from transformer.plugins.contracts import Plugin
from transformer.scenario import Scenario


def transform(
    scenarios_path: Union[str, Path], plugins: Sequence[Plugin] = ()
) -> py.Program:
    return locustfile([Scenario.from_path(Path(scenarios_path), plugins)])


def main(scenarios_path: Union[str, Path], plugins: Sequence[Plugin] = ()) -> str:
    """
    Converts a WeightedFilePaths into a Locustfile.
    """

    return str(transform(Path(scenarios_path), plugins))
