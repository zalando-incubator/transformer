from pathlib import Path
from typing import cast

import tomlkit
from tomlkit.toml_document import TOMLDocument


def pyproject() -> TOMLDocument:
    with Path(__file__).parent.parent.joinpath("pyproject.toml").open() as f:
        pyproject = f.read()
    return tomlkit.parse(pyproject)


def version() -> str:
    return cast(str, pyproject()["tool"]["poetry"]["version"])
