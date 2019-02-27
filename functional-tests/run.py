#!/usr/bin/env python
import enum
import logging
import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path
from typing import Optional, NewType, cast, Sequence, NamedTuple, Iterator, Iterable

Venv = NewType("Venv", Path)
Wheel = NewType("Wheel", Path)

THIS_PATH = Path(__file__)


class ExitCode(enum.IntEnum):
    Ok = 0
    UnknownError = enum.auto()
    NoWheel = enum.auto()
    NoTests = enum.auto()
    TestFailures = enum.auto()


def create_virtualenv() -> Venv:
    d = tempfile.mkdtemp()
    venv.create(d, with_pip=True)
    return cast(Venv, Path(d))


def build_transformer_wheel() -> Optional[Wheel]:
    root_path = THIS_PATH.parent.parent

    dist_path = root_path / "dist"

    shutil.rmtree(dist_path, ignore_errors=True)

    logging.info("Building the project with Poetry ...")
    subprocess.run(["poetry", "build"], cwd=root_path, check=True)

    return next((cast(Wheel, f) for f in dist_path.glob("*.whl")), None)


def install_wheel_in_venv(wheel: Wheel, venv: Venv) -> None:
    logging.info(f"Installing {wheel} in {venv} ...")
    res = run_in_venv(
        ["pip", "install", "--upgrade", str(wheel.resolve())],
        venv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        logging.error("Installing Transformer's wheel failed!")
        logging.info("--- stdout was:")
        print(res.stdout)
        logging.info("--- stderr was:")
        print(res.stderr)
        raise ValueError("failed installing Transformer's wheel")


def run_in_venv(
    cmd: Sequence[str], venv: Venv, **kwargs
) -> subprocess.CompletedProcess:
    path = os.pathsep.join([f"{venv}/bin", os.environ["PATH"]])
    return subprocess.run(cmd, env={"PATH": path, "VIRTUAL_ENV": str(venv)}, **kwargs)


def program_for_running(script: Path) -> Optional[str]:
    ext = script.suffix
    if ext == ".py":
        return "python3"
    if ext == ".sh":
        return "sh"
    if ext == ".bash":
        return "bash"
    return None


class TestCase(NamedTuple):
    script: Path
    program: str


def enumerate_test_cases(directory: Path) -> Iterator[TestCase]:
    for path in directory.glob("**/test-*"):
        if not path.is_file() or path.samefile(THIS_PATH):
            continue
        prog = program_for_running(path)
        if not prog:
            logging.warning(f"Ignoring test case {path}: unsupported file extension.")
            continue
        yield TestCase(script=path, program=prog)


def run_tests(test_cases: Iterable[TestCase], v: Venv) -> ExitCode:
    w = build_transformer_wheel()
    if not w:
        logging.fatal("No wheel: aborting.")
        return ExitCode.NoWheel

    install_wheel_in_venv(w, v)

    nb_scripts_run = 0
    nb_scripts_failed = 0

    for tc in test_cases:
        logging.info(f"--- Running test case {tc.script} with {tc.program} ...")
        process = run_in_venv([tc.program, str(tc.script)], v)
        nb_scripts_run += 1
        if process.returncode == 0:
            logging.info("--- ok")
        else:
            logging.info(f"--- FAIL: exitcode = {process.returncode}")
            nb_scripts_failed += 1

    if nb_scripts_failed == 0:
        logging.info(f"Test cases run: {nb_scripts_run}. No failures.")
        return ExitCode.Ok
    else:
        logging.error(
            f"Test cases run: {nb_scripts_run}. Failures: {nb_scripts_failed}!"
        )
        return ExitCode.TestFailures


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s"
    )

    test_cases = list(enumerate_test_cases(THIS_PATH.parent))
    if not test_cases:
        logging.fatal("No test cases to run!")
        exit(ExitCode.NoTests)
    logging.info(f"{len(test_cases)} test cases selected:")
    for tc in test_cases:
        logging.info(f"\t{tc.script} ({tc.program})")

    logging.info("Creating a virtualenv ...")
    v = create_virtualenv()
    logging.info(f"Virtualenv created in {v}.")

    try:
        exitcode = run_tests(test_cases, v)
    except Exception:
        logging.exception("Caught exception at top level.")
        exitcode = ExitCode.UnknownError
    finally:
        logging.info(f"Deleting virtualenv {v} ...")
        shutil.rmtree(v)

    exit(exitcode)
