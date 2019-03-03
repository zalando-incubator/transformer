"""
:mod:transformer.transform -- Entrypoint functions
==================================================

Defines user-facing functions performing all or most of the HAR-to-locustfile
conversion.
"""
import warnings
from pathlib import Path
from typing import Sequence, Union, Iterable, TextIO, Iterator, TypeVar

import transformer.plugins as plug
from transformer.locust import locustfile, locustfile_lines
from transformer.plugins import sanitize_headers, Contract
from transformer.plugins.contracts import Plugin
from transformer.scenario import Scenario

DEFAULT_PLUGINS = (sanitize_headers.plugin,)


def transform(
    scenarios_path: Union[str, Path],
    plugins: Sequence[Plugin] = (),
    with_default_plugins: bool = True,
) -> str:
    """
    This function is deprecated and will be removed in a future version.
    Do not rely on it.
    Reason: It only accepts one scenario path at a time, and requires plugins
    to be already resolved (and therefore that users use
    transformer.plugins.resolve, which is kind of low-level). Both dumps & dump
    lift these constraints and have a more familiar naming
    (see json.dump/s, etc.).
    Deprecated since: v1.0.2.
    """
    warnings.warn(DeprecationWarning("transform: use dump or dumps instead"))
    if with_default_plugins:
        plugins = (*DEFAULT_PLUGINS, *plugins)
    return locustfile([Scenario.from_path(Path(scenarios_path), plugins)])


LaxPath = Union[str, Path]
PluginName = str


def dumps(
    scenario_paths: Iterable[LaxPath],
    plugins: Sequence[PluginName] = (),
    with_default_plugins: bool = True,
) -> str:
    """
    Transforms the provided *scenario_paths* using the provided *plugins*,
    and returns the resulting locustfile code as a string.

    See also: :func:`dump`

    :param scenario_paths: paths to scenario files (HAR) or directories
    :param plugins: names of plugins to use
    :param with_default_plugins: whether the default plugins should be used in
        addition to those provided (recommended: True)
    """
    return "\n".join(_dump_as_lines(scenario_paths, plugins, with_default_plugins))


def dump(
    file: TextIO,
    scenario_paths: Iterable[LaxPath],
    plugins: Sequence[PluginName] = (),
    with_default_plugins: bool = True,
) -> None:
    """
    Transforms the provided *scenario_paths* using the provided *plugins*,
    and writes the resulting locustfile code in the provided *file*.

    See also: :func:`dumps`

    :param file: an object with a `writelines` method (as specified by
        io.TextIOBase), e.g. `sys.stdout` or the result of `open`.
    :param scenario_paths: paths to scenario files (HAR) or directories.
    :param plugins: names of plugins to use.
    :param with_default_plugins: whether the default plugins should be used in
        addition to those provided (recommended: True).
    """
    file.writelines(
        intersperse("\n", _dump_as_lines(scenario_paths, plugins, with_default_plugins))
    )


def _dump_as_lines(
    scenario_paths: Iterable[LaxPath],
    plugins: Sequence[PluginName],
    with_default_plugins: bool,
) -> Iterator[str]:
    plugins = [p for name in plugins for p in plug.resolve(name)]
    if with_default_plugins:
        plugins = (*DEFAULT_PLUGINS, *plugins)

    plugins_for = plug.group_by_contract(plugins)

    scenarios = [
        Scenario.from_path(
            path, plugins_for[Contract.OnTask], plugins_for[Contract.OnTaskSequence]
        ).apply_plugins(plugins_for[Contract.OnScenario])
        for path in scenario_paths
    ]

    yield from locustfile_lines(scenarios, plugins_for[Contract.OnPythonProgram])


T = TypeVar("T")


def intersperse(delim: T, iterable: Iterable[T]) -> Iterator[T]:
    """
    >>> list(intersperse(",", "a"))
    ['a']
    >>> list(intersperse(",", ""))
    []
    >>> list(intersperse(",", "abc"))
    ['a', ',', 'b', ',', 'c']
    >>> list(intersperse(",", ["a", "b", "c"]))
    ['a', ',', 'b', ',', 'c']
    """
    it = iter(iterable)
    try:
        yield next(it)
    except StopIteration:
        return
    for x in it:
        yield delim
        yield x
