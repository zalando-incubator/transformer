#!/usr/bin/env python3

"""
Build and publish this package to PyPI as a prerelease.

This script adds a "developmental release segment" [1] to the version identifier
stored in pyproject.toml, and then invokes "poetry publish --build".

[1]: https://www.python.org/dev/peps/pep-0440/#developmental-releases
"""
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import tomlkit

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s"
)

pyproject_path = Path("pyproject.toml")
logging.info(f"Reading {pyproject_path} ...")
pyproject_data = tomlkit.parse(pyproject_path.read_text())

dev_int = datetime.now().strftime("%Y%m%d%H%M%S")
version = pyproject_data["tool"]["poetry"]["version"]
dev_version = f"{version}.dev{dev_int}"
logging.info(f"Updating version: {version} -> {dev_version}")
pyproject_data["tool"]["poetry"]["version"] = dev_version

logging.info(f"Writing new config to {pyproject_path} ...")
pyproject_path.write_text(tomlkit.dumps(pyproject_data))

subprocess.run(["poetry", "publish", "--build"], check=True)
