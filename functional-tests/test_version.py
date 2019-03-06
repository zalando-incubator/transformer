import subprocess


def test_version():
    expected = "1.1.0"
    actual = (
        subprocess.run(["transformer", "--version"], check=True, stdout=subprocess.PIPE)
        .stdout.strip()
        .decode()
    )
    assert actual == expected
