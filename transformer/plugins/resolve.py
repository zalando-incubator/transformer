import importlib
import inspect
import logging
from types import ModuleType
from typing import Iterator

from transformer.plugins import contracts
from transformer.plugins.contracts import Plugin


def resolve(name: str) -> Iterator[Plugin]:
    """
    Transform a plugin name into the corresponding, actual plugins.

    The name of a plugin is the name of a Python module containing (at least)
    one function which name begins with "plugin" and which is annotated
    according to one of the "plugin contracts" (defined in the contracts module).
    The "resolve" function loads that module and returns these plugin functions
    found inside the module.
    """
    try:
        module = importlib.import_module(name)
    except ImportError as err:
        logging.error(f"failed to import plugin module {name!r}: {err}")
        return iter(())

    return load_plugins_from_module(module)


PLUGIN_PREFIX = "plugin"


def load_plugins_from_module(module: ModuleType) -> Iterator[Plugin]:
    if not inspect.ismodule(module):
        raise TypeError(f"expected a module, got {module!r}")
    at_least_once = False
    for obj_name, obj in inspect.getmembers(module, inspect.isfunction):
        if obj_name.startswith(PLUGIN_PREFIX):
            valid = contracts.isvalid(Plugin, obj)
            if not valid:
                logging.warning(f"ignoring {obj_name}: {valid.reason}")
            else:
                at_least_once = True
                yield obj
        else:
            logging.debug(f"ignoring {obj_name}: doesn't start with {PLUGIN_PREFIX!r}")

    if not at_least_once:
        logging.error(f"module {module} doesn't contain plugin functions")
