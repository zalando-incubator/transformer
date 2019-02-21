import logging
import random
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest
from hypothesis import given
from hypothesis._strategies import permutations

from transformer.plugins.contracts import plugin, Contract
from .resolve import load_plugins_from_module, resolve, NoPluginError


@pytest.fixture()
def module_root(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    return tmp_path


class TestResolve:
    def test_raises_for_module_not_found(self):
        modname = f"that_module_does_not_exist.{uuid.uuid4().hex}"
        with pytest.raises(ImportError):
            list(resolve(modname))  # must force evaluation of the generator

    def test_calls_load_plugins_from_module_with_module(self, module_root: Path):
        modname = "ab.cd.ef"
        modpath = Path(*modname.split(".")).with_suffix(".py")
        Path(module_root, modpath.parent).mkdir(parents=True)
        with Path(module_root, modpath).open("w") as f:
            f.write("from transformer.plugins.contracts import plugin, Contract\n")
            f.write("@plugin(Contract.OnTask)\n")
            f.write("def f(t):\n")
            f.write("   ...\n")
            f.write("def helper(t):\n")
            f.write("   ...\n")

        plugins = list(resolve(modname))
        assert len(plugins) == 1
        f = plugins[0]
        assert callable(f)
        assert f.__name__ == "f"

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

    def not_a_plugin(_):
        ...

    def plugin_not_a_plugin_either(_):
        ...

    @plugin(Contract.OnTask)
    def plugin_valid(_):
        ...

    @given(permutations((not_a_plugin, plugin_not_a_plugin_either, plugin_valid)))
    def test_ignores_non_plugin_stuff_in_module(self, module, caplog, functions):
        for f in functions:
            module.__dict__[f.__name__] = f

        caplog.clear()
        caplog.set_level(logging.DEBUG)
        plugins = list(load_plugins_from_module(module))

        plugin_valid = next(f for f in functions if f.__name__ == "plugin_valid")
        assert plugins == [plugin_valid]

        non_plugin_functions = {f for f in functions if f is not plugin_valid}
        print(f">>> log messages: {caplog.messages}")
        for f in non_plugin_functions:
            assert any(
                f.__name__ in msg for msg in caplog.messages
            ), "ignored function names should be logged"

    def test_raises_for_modules_without_any_plugin(self, module):
        with pytest.raises(NoPluginError, match=module.__name__):
            # must force evaluation of the generator
            list(load_plugins_from_module(module))
