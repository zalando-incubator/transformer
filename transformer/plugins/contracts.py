"""
:mod:`transformer.plugins.contracts` -- Contracts for Plugin Authors
====================================================================

This module defines the various :ref:`Transformer contracts <contracts>`
and their helper functions.
"""
import enum
from collections import defaultdict
from typing import NewType, Iterable, TypeVar, List, DefaultDict


class Contract(enum.Flag):
    """
    Enumeration of all supported :ref:`plugin contracts <contracts>`.
    Each specific contract defines a way for plugins to be used in Transformer.

    Any Python function may become a Transformer plugin by announcing that
    it implements at least one contract, using the :func:`@plugin <plugin>`
    decorator.
    """

    OnTask = enum.auto()  #: The :term:`OnTask` contract.
    OnScenario = enum.auto()  #: The :term:`OnScenario` contract.
    OnPythonProgram = enum.auto()  #: The :term:`OnPythonProgram` contract.

    # Historically Transformer has only one plugin contract, which transformed a
    # sequence of Task objects into another such sequence. Operating on a full list
    # of tasks (instead of task by task) offered more leeway: a plugin could e.g.
    # add a new task, or change only the first task.
    # However this OnTaskSequence model is too constraining for some use-cases,
    # e.g. when a plugin needs to inject code in the global scope, and having to
    # deal with a full, immutable list of tasks in plugins that independently
    # operate on each task implies a lot of verbosity and redundancy.
    # For these reasons, other plugin contracts were created to offer a more
    # varied choice for plugin implementers.
    # See https://github.com/zalando-incubator/Transformer/issues/10.
    OnTaskSequence = enum.auto()  #: Deprecated.


Plugin = NewType("Plugin", callable)


class InvalidContractError(ValueError):
    """
    Raised for plugin functions associated with invalid contracts.

    What an "invalid contract" represents is not strictly specified,
    but this includes at least objects that are not members of the Contract
    enumeration.
    """


class InvalidPluginError(ValueError):
    """
    Raised when trying to use as plugin a function that has not been marked
    as such.
    """


def plugin(c: Contract):
    """
    Documented in dev.rst.
    """
    if not isinstance(c, Contract):
        suggestions = (f"@plugin(Contract.{x.name})" for x in Contract)
        raise InvalidContractError(
            f"{c!r} is not a {Contract.__qualname__}. "
            f"Did you mean {', '.join(suggestions)}?"
        )

    def _decorate(f: callable) -> callable:
        f._transformer_plugin_contract = c
        return f

    return _decorate


def contract(f: Plugin) -> Contract:
    """
    Returns the contract associated to a plugin function.

    :raise InvalidPluginError: if f is not a plugin.
    """
    try:
        return getattr(f, "_transformer_plugin_contract")
    except AttributeError:
        raise InvalidPluginError(f) from None


_T = TypeVar("_T")


def apply(plugins: Iterable[Plugin], init: _T) -> _T:
    """
    Applies each plugin to init in order, and returns the result.

    This just wraps a very simple but common operation.
    """
    for p in plugins:
        init = p(init)
    return init


_BASE_CONTRACTS = (
    Contract.OnTask,
    Contract.OnTaskSequence,
    Contract.OnScenario,
    Contract.OnPythonProgram,
)


def group_by_contract(plugins: Iterable[Plugin]) -> DefaultDict[Contract, List[Plugin]]:
    """
    Groups plugins in lists according to their contracts.
    Each plugin is found in as many lists as it implements base contracts.
    Lists keep the order of the original plugins iterable.
    """
    res = defaultdict(list)
    for p in plugins:
        c = contract(p)
        for bc in _BASE_CONTRACTS:
            if c & bc:  # Contract is an enum.Flag: & computes the intersection.
                res[bc].append(p)
    return res
