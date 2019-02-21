import importlib
import inspect
import logging
from types import ModuleType
from typing import Iterator

from transformer.plugins.contracts import (
    Plugin,
    Contract,
    InvalidContractError,
    contract,
    InvalidPluginError,
)


def resolve(name: str) -> Iterator[Plugin]:
    """
    Transform a plugin name into the corresponding, actual plugins.

    The name of a plugin is the name of a Python module containing (at least)
    one function decorated with @plugin (from the contracts module).
    The "resolve" function loads that module and returns these plugin functions
    found inside the module.

    :raise ImportError: if name does not match an accessible module.
    :raise TypeError: from load_load_plugins_from_module.
    :raise InvalidContractError: from load_load_plugins_from_module.
    :raise NoPluginError: from load_load_plugins_from_module.
    """
    module = importlib.import_module(name)

    yield from load_plugins_from_module(module)


class NoPluginError(ValueError):
    """
    Raised for Python modules that should but don't contain any plugin function.
    """


def load_plugins_from_module(module: ModuleType) -> Iterator[Plugin]:
    """
    :param module: Python module from which to load plugin functions.
    :raise TypeError: if module is not a Python module.
    :raise InvalidContractError: if a function is associated to an invalid contract.
    :raise NoPluginError: if module doesn't contain at least one plugin function.
    """
    if not inspect.ismodule(module):
        raise TypeError(f"expected a module, got {module!r}")

    nb_plugins = 0

    for _, obj in inspect.getmembers(module, inspect.isfunction):
        try:
            c = contract(obj)
        except InvalidPluginError:
            logging.debug(f"ignoring {_n(obj)}: not decorated with @plugin")
            continue

        if not isinstance(c, Contract):
            msg = f"{_n(obj)} associated to an invalid contract {c!r}"
            raise InvalidContractError(msg)

        nb_plugins += 1
        yield obj

    if nb_plugins < 1:
        raise NoPluginError(module)


def _n(x) -> str:
    return getattr(x, "__qualname__", None) or repr(x)
