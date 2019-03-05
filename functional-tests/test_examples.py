import subprocess
from pathlib import Path


def run_example(example_name: str) -> subprocess.CompletedProcess:
    har_path = Path(__file__).parent.parent.joinpath("examples", example_name)
    return subprocess.run(
        ["transformer", str(har_path)], timeout=2, check=True, stdout=subprocess.PIPE
    )


def test_example_google():
    ex = run_example("www.google.com.har")
    assert len(ex.stdout) > 100
    assert b"https://consent.google.com" in ex.stdout


def test_example_zalando():
    ex = run_example("en.zalando.de.har")
    assert len(ex.stdout) > 100
    assert b"https://en.zalando.de/?_rfl=de" in ex.stdout
