from pathlib import Path

from .cli import read_config


class TestReadConfig:
    def test_paths_from_env(self, monkeypatch):
        monkeypatch.setenv("TRANSFORMER_INPUT_PATHS", """["/x/y", "a/b"]""")
        conf = read_config([])
        assert conf.input_paths == (Path("/x/y"), Path("a/b"))

    def test_paths_from_cli(self):
        conf = read_config(["/x/y", "a/b"])
        assert conf.input_paths == (Path("/x/y"), Path("a/b"))

    def test_paths_from_cli_overwrite_those_from_env(self, monkeypatch):
        monkeypatch.setenv("TRANSFORMER_INPUT_PATHS", """["/x/y", "a/b"]""")
        conf = read_config(["u/v/w"])
        assert conf.input_paths == (Path("u/v/w"),)

    def test_plugins_from_env(self, monkeypatch):
        monkeypatch.setenv("TRANSFORMER_PLUGINS", """["a", "b.c.d"]""")
        conf = read_config([])
        assert conf.plugins == ("a", "b.c.d")

    def test_plugins_from_cli(self):
        conf = read_config(["-p", "a", "XXX", "--plugin", "b.c.d"])
        assert conf.plugins == ("a", "b.c.d")

    def test_merge_plugins_from_env_and_cli(self, monkeypatch):
        monkeypatch.setenv("TRANSFORMER_PLUGINS", """["a", "b.c.d"]""")
        conf = read_config(["-p", "e.f", "XXX", "--plugin", "g"])
        assert conf.plugins == ("a", "b.c.d", "e.f", "g")
