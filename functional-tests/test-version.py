import subprocess

expected = "1.0.2"

actual = (
    subprocess.run(["transformer", "--version"], check=True, stdout=subprocess.PIPE)
    .stdout.strip()
    .decode()
)

assert actual == expected, f"expected {expected!r}, got {actual!r}"
