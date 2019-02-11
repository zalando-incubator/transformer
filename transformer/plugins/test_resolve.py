import logging
import random
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest

from transformer.task import Task2
from .resolve import load_plugins_from_module, resolve


@pytest.fixture()
def module_root(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    return tmp_path


class TestResolve:
    def test_returns_empty_and_logs_for_module_not_found(self, caplog):
        modname = f"that_module_does_not_exist.{uuid.uuid4().hex}"
        assert list(resolve(modname)) == []
        assert f"failed to import plugin module {modname!r}" in caplog.text

    def test_calls_load_plugins_from_module_with_module(self, module_root: Path):
        modname = "ab.cd.ef"
        modpath = Path(*modname.split(".")).with_suffix(".py")
        Path(module_root, modpath.parent).mkdir(parents=True)
        with Path(module_root, modpath).open("w") as f:
            f.write("from transformer.plugins.contracts import Task2\n")
            f.write("def plugin_f(t: Task2) -> Task2:\n")
            f.write("   ...\n")
        plugins = list(resolve(modname))
        assert len(plugins) == 1
        f = plugins[0]
        assert f.__name__ == "plugin_f"

    def test_resolve_is_exported_by_the_transformer_plugins_module(self):
        try:
            from transformer.plugins import resolve
        except ImportError:
            pytest.fail("resolve should be exported by transformer.plugins")


@pytest.fixture()
def module() -> ModuleType:
    """Creates and returns an empty module."""
    return ModuleType(f"fake_{random.randint(0, 99999999)}")


class TestLoadPluginsFromModule:
    def test_raises_error_for_non_module(self):
        class A:
            pass

        with pytest.raises(TypeError):
            # Iterators are lazy, we need list()
            list(load_plugins_from_module(A))

    def test_ignores_non_plugin_stuff_in_module(self, module, caplog):
        def signature_not_a_plugin(_: Task2) -> Task2:
            ...

        def plugin_prefixed_but_no():
            ...

        def plugin_valid(_: Task2) -> Task2:
            ...

        non_plugin_functions = (signature_not_a_plugin, plugin_prefixed_but_no)
        functions = (*non_plugin_functions, plugin_valid)
        for f in functions:
            module.__dict__[f.__name__] = f

        caplog.clear()
        caplog.set_level(logging.DEBUG)
        plugins = list(load_plugins_from_module(module))

        assert plugins == [plugin_valid]

        print(f">>> log messages: {caplog.messages}")
        for f in non_plugin_functions:
            assert any(
                f.__name__ in msg for msg in caplog.messages
            ), "ignored function names should be logged"

    def test_empty_iterator_for_modules_without_any_plugin(self, module, caplog):
        plugins = list(load_plugins_from_module(module))
        assert plugins == []
        assert module.__name__ in caplog.text
