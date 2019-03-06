#!/usr/bin/env python3

"""
update-version.py: Execute the first steps of Transformer's release process.

See https://transformer.readthedocs.io/en/latest/Versioning.html#release-process
for details.

Usage:
    update-version.py INCREMENT
    update-version.py --help
"""
import enum
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Sequence

import dataclasses
import packaging.version
import pygments
import tomlkit
from dataclasses import dataclass
from docopt import docopt
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.diff import DiffLexer


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, s: str) -> "Version":
        v = packaging.version.parse(s)
        return Version(*v.release)

    def __str__(self) -> str:
        return ".".join((str(self.major), str(self.minor), str(self.patch)))


@dataclass
class Patch:
    target: os.PathLike
    lines: Sequence[str]

    def apply(self) -> bool:
        target = os.fspath(self.target)
        with tempfile.NamedTemporaryFile("a+") as f:
            f.write("\n".join(self.lines))
            f.write("\n")
            f.seek(0)
            result = subprocess.run(["patch", "-u", target], stdin=f)
        if result.returncode == 0:
            return True
        logging.error(f"failed to apply patch")
        logging.info(f"patch was {self!r}")
        return False

    def pretty(self) -> str:
        lines = list(self.lines)
        lines[0] += f" {self.target}"  # include target name in comments
        return pygments.highlight("\n".join(lines), DiffLexer(), TerminalFormatter())


def pyproject_patch(old_v: Version, new_v: Version) -> Patch:
    return Patch(
        target=Path("pyproject.toml"),
        lines=["@@ -3 +3 @@", f'-version = "{old_v}"', f'+version = "{new_v}"'],
    )


def sphinx_patch(old_v: Version, new_v: Version) -> Patch:
    old_short = f"{old_v.major}.{old_v.minor}"
    new_short = f"{new_v.major}.{new_v.minor}"
    return Patch(
        target=Path("docs", "conf.py"),
        lines=[
            "@@ -25,5 +25,5 @@",
            " # The short X.Y version",
            f'-version = "{old_short}"',
            f'+version = "{new_short}"',
            " # The full version, including alpha/beta/rc tags",
            f'-release = "{old_v}"',
            f'+release = "{new_v}"',
            " ",
        ],
    )


def changelog_patch(old_v: Version, new_v: Version) -> Patch:
    new_diff_url = (
        "https://github.com/zalando-incubator/transformer/compare/"
        f"v{old_v}...v{new_v}"
    )
    release_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return Patch(
        target=Path("docs", "Changelog.rst"),
        lines=[
            "@@ -17,2 +17,13 @@",
            " ",
            f"+.. _v{new_v}:",
            "+",
            f"+v{new_v}",
            "+" + ("=" * (1 + len(str(new_v)))),
            "+",
            f"+- Release date: {release_date}",
            "+",
            "+- Diff__.",
            "+",
            f"+__ {new_diff_url}",
            "+",
            f" .. _v{old_v}:",
        ],
    )


def functional_test_patch(old_v: Version, new_v: Version) -> Patch:
    return Patch(
        target=Path("functional-tests", "test_version.py"),
        lines=[
            "@@ -4,3 +4,3 @@",
            " def test_version():",
            f'-    expected = "{old_v}"',
            f'+    expected = "{new_v}"',
            '     actual = ("""',
        ],
    )


class Increment(enum.IntEnum):
    MAJOR = 0
    MINOR = 1
    PATCH = 2


def increment_version(v: Version, incr: Increment) -> Version:
    values = list(dataclasses.astuple(v))
    values[incr.value] += 1
    for i in range(incr.value + 1, max(Increment).value + 1):
        values[i] = 0
    return Version(*values)


def pyproject_version(pyproject_path: os.PathLike) -> Version:
    pyproject_data = tomlkit.parse(Path(pyproject_path).read_text())
    return Version.parse(str(pyproject_data["tool"]["poetry"]["version"]))


def run():
    opts = docopt(__doc__)
    incr_str = opts["INCREMENT"].upper()
    try:
        incr: Increment = Increment[incr_str]
    except KeyError:
        logging.fatal(f"Invalid increment value {incr_str!r}")
        logging.info(f"Expecting one of {[i.name for i in Increment]}")
        raise  # PyCharm doesn't get that exit() prevents increments from not existing

    # Find the current version

    pyproject_path = Path("pyproject.toml")
    logging.info(f"Reading {pyproject_path} ...")
    old_version = pyproject_version(pyproject_path)
    logging.info(f"Current version: {old_version}")

    # Compute the new version, according to *incr*.
    new_version = increment_version(old_version, incr)
    logging.info(f"New version: {new_version} ({old_version} + {incr.name})")

    # Compute the corresponding patches.
    patches = [
        pyproject_patch(old_version, new_version),
        changelog_patch(old_version, new_version),
        sphinx_patch(old_version, new_version),
        functional_test_patch(old_version, new_version),
    ]

    # Show the patches, in case users want to reverse them later, and apply them.
    logging.info("Applying these patches:")
    expected_successes = len(patches)
    actual_successes = 0
    for patch in patches:
        print(patch.pretty())
        if patch.apply():
            actual_successes += 1
        print()
    logging.info(f"Patched {actual_successes}/{expected_successes} of expected files.")
    if actual_successes < expected_successes:
        raise RuntimeError()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s"
    )
    try:
        run()
    except Exception:
        exit(1)
