import re
import subprocess


def test_version():
    expected_pattern = re.compile(
        r"\b [0-9]+ \. [0-9]+ \. [0-9]+ ([ab] [0-9]+)? \b", re.X
    )
    actual = (
        subprocess.run(["transformer", "--version"], check=True, stdout=subprocess.PIPE)
        .stdout.strip()
        .decode()
    )
    assert expected_pattern.match(actual)
