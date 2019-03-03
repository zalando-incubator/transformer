"""
:mod:`transformer.scenario` -- Grouping related tasks into scenarios
====================================================================

.. |Scenario| replace:: :class:`Scenario`

Transformer creates a |Scenario| object for each HAR file it reads, so each
:term:`task` (representing an HTTP request in a HAR file) is part of a
:term:`scenario`.
Transformer also creates |Scenario| objects for directories that contain
HAR files, so a :term:`scenario` can also be part of another :term:`scenario`.

To sum up, |Scenario| objects form a tree_, the leaves of which are all
:term:`task` objects.
This hierarchical structure maps cleanly to Locust's :class:`~locust.core.TaskSet`
objects, which can also be nested and have a weight.

.. _tree: https://en.wikipedia.org/wiki/Tree_(data_structure)
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Sequence, Mapping, Union, Set, List, Optional, Dict, Tuple

import dataclasses
from dataclasses import dataclass

import transformer.plugins as plug
from transformer.naming import to_identifier
from transformer.plugins.contracts import Plugin
from transformer.request import Request
from transformer.task import Task, Task2

WEIGHT_FILE_SUFFIX = ".weight"
DEFAULT_WEIGHT = 1


class SkippableScenarioError(ValueError):  # noqa: B903
    """
    Raised when a Scenario cannot be created from the provided input path.

    If related to the creation of a Scenario B inside a larger Scenario A (i.e.
    B would be in A.children), A catches this exception, logs a warning, and
    moves on to the next potential child.
    """

    def __init__(self, scenario_path: Path, reason: Union[Exception, str]) -> None:
        self.path = scenario_path
        self.reason = reason


class DanglingWeightError(SkippableScenarioError):
    """
    Raised when a scenario directory contains weight files that don't correspond
    to any scenario.
    """

    pass


class CollidingScenariosError(SkippableScenarioError):
    """
    Raised when scenarios created from different paths end up having the same
    name.

    The only way this happens is if the paths are identical save for their
    extension (e.g. ``.har`` vs ``.json``), or if there is a bug (collision) in
    :func:`~transformer.naming.to_identifier` (which should never happen).
    """

    pass


class WeightValueError(ValueError):  # noqa: B903
    """
    Raised when the weight file associated to a scenario contains errors.
    """

    def __init__(self, scenario_path: Path, reason: Union[Exception, str]) -> None:
        self.path = scenario_path
        self.reason = reason


@dataclass
class Scenario:
    """
    A web browsing session that we want to emulate, i.e. a sequence of
    :term:`tasks <task>` to be performed.

    .. attribute:: name

        :any:`str` -- Name of the corresponding :class:`~locust.core.TaskSet`.

    .. attribute:: children

        |Sequence| [ :class:`~transformer.task.Task2` :data:`| <typing.Union>`
        :class:`Scenario` ] --
        Tasks and scenarios that are part of this scenario.

    .. attribute:: origin

        :data:`~typing.Optional` :class:`~pathlib.Path` --
        Path to the HAR file or directory this scenario represents.

    .. attribute:: weight
       :annotation: = 1

       :any:`int` -- Weight of this scenario.
       See :ref:`Specifying-weights` and :ref:`Hierarchical-scenarios` for details.
    """

    name: str
    children: Sequence[Union[Task, Task2, "Scenario"]]
    origin: Optional[Path]
    weight: int = 1

    @classmethod
    def from_path(
        cls,
        path: Path,
        plugins: Sequence[Plugin] = (),
        ts_plugins: Sequence[Plugin] = (),
        short_name: bool = False,
    ) -> "Scenario":
        """
        Makes a :class:`Scenario` (possibly containing sub-scenarios) out of
        the provided *path*, which may point to either:

        - a HAR file (like :file:`x/y/z.har`),

        - a scenario directory (a directory containing HAR files or other
          scenario directories).

        :raise SkippableScenarioError: if path is neither a directory nor a HAR file,
            or is a directory containing dangling weight files
        :param path: path to the HAR file or scenario directory.
        :param plugins: list of :term:`OnScenario` plugins to apply.
        :param ts_plugins: deprecated -- for backward compatibility only.
        :param short_name: whether the returned scenarios have names based only
            on their path's basename, instead of the full path.
            By default *False* to avoid generating homonym scenarios
            (and therefore homonym :class:~locust.core.TaskSet` classes),
            but *True* when generating sub-scenarios (:attr:`children`) from
            a directory *path* (because then the names are "scoped" by
            the parent directory).
        """
        if path.is_dir():
            return cls.from_dir(
                path, plugins, ts_plugins=ts_plugins, short_name=short_name
            )
        else:
            return cls.from_har_file(
                path, plugins, ts_plugins=ts_plugins, short_name=short_name
            )

    @classmethod
    def from_dir(
        cls,
        path: Path,
        plugins: Sequence[Plugin],
        ts_plugins: Sequence[Plugin],
        short_name: bool,
    ) -> "Scenario":
        """
        Makes a :class:`Scenario` out of the provided directory *path*.

        *path* must represent a "scenario directory", which contains at least
        one HAR file or another scenario directory.
        Symbolic link loops are not checked but forbidden!

        There may exist a weight file :file:`{path}.weight`.
        If so, its contents will be used as :attr:`weight` after calling
        :meth:`weight_from_path`.

        Errors are handled this way:

        #. If *path* itself cannot be transformed into a scenario,
           raise :exc:`SkippableScenarioError`.

        #. For each child of *path*, apply (1) but catch the exception and
           display a warning about skipping that child.
           (If all children are skipped, (1) applies to *path* itself.)

        Therefore:

        - If the directory contains weight files that don't match any HAR file or
          subdirectory, an error is emitted as this is probably a mistake.

        - If the directory contains files or directories that cannot be converted
          into scenarios (e.g. non-JSON files or :file:`.git` directories),
          a message is emitted and the file or subdirectory is skipped.

        :param path: path to the directory.
        :param plugins: list of :term:`OnScenario` plugins to apply.
        :param ts_plugins: deprecated -- for backward compatibility only.
        :param short_name: whether to simplify the resulting
            :class:`~locust.core.TaskSet` class name. If *short_name* is *False*,
            that class name is guaranteed to be unique across all TaskSets of the
            locustfile, but this is generally not necessary and results in less
            readable class names.
        :raise SkippableScenarioError: if the directory contains dangling weight
            files or no sub-scenarios.
        """
        try:
            children = list(path.iterdir())
        except OSError as err:
            raise SkippableScenarioError(path, err)

        weight_files: Set[Path] = {
            child for child in children if child.suffix == WEIGHT_FILE_SUFFIX
        }

        scenarios: List[Scenario] = []
        for child in children:
            if child in weight_files:
                continue
            try:
                scenario = cls.from_path(
                    child, plugins, ts_plugins=ts_plugins, short_name=True
                )
            except SkippableScenarioError as err:
                logging.warning(
                    "while searching for HAR files, skipping %s: %s", child, err.reason
                )
            else:
                scenarios.append(scenario)

        cls._check_dangling_weights(path, scenarios, weight_files)
        if not scenarios:
            raise SkippableScenarioError(path, "no scenarios inside the directory")
        cls._check_name_collisions(path, scenarios)

        return Scenario(
            name=to_identifier(path.with_suffix("").name if short_name else str(path)),
            children=tuple(scenarios),
            origin=path,
            weight=cls.weight_from_path(path),
        )

    @classmethod
    def _check_name_collisions(cls, path: Path, scenarios: List["Scenario"]):
        scenarios_by_name: Dict[str, List[Scenario]] = defaultdict(list)
        for s in scenarios:
            scenarios_by_name[s.name].append(s)
        colliding_paths: Set[Tuple[Path, ...]] = {
            tuple(x.origin for x in xs)
            for xs in scenarios_by_name.values()
            if len(xs) > 1
        }
        if colliding_paths:
            groups = "; ".join(
                " vs ".join(repr(s.name) for s in group) for group in colliding_paths
            )
            logging.error(
                "%s contains scenarios with colliding names: %s", path, groups
            )
            raise CollidingScenariosError(path, "scenarios have colliding names")

    @classmethod
    def _check_dangling_weights(cls, path, scenarios, weight_files):
        scenario_names = {s.origin.with_suffix("").name for s in scenarios}
        dangling_weight_files = [
            f for f in weight_files if f.with_suffix("").name not in scenario_names
        ]
        if dangling_weight_files:
            hint = ", ".join(str(f) for f in dangling_weight_files)
            logging.error(
                "%s contains weight files that don't correspond to any scenarios: %s",
                path,
                hint,
            )
            logging.info(
                "For any value of X, if there exists a weight file X.weight, "
                "there must exist either an X.har file or an X scenario subdirectory."
            )
            raise DanglingWeightError(path, "contains dangling weight files")

    @classmethod
    def from_har_file(
        cls,
        path: Path,
        plugins: Sequence[Plugin],
        ts_plugins: Sequence[Plugin],
        short_name: bool,
    ) -> "Scenario":
        """
        Creates a Scenario given a HAR file.

        :raise SkippableScenarioError: if path is unreadable or not a HAR file
        """
        try:
            with path.open() as file:
                har = json.load(file)
            requests = Request.all_from_har(har)
            tasks = Task.from_requests(requests)

            # TODO: Remove this when Contract.OnTaskSequence is removed.
            tasks = plug.apply(ts_plugins, tasks)

            # TODO: Remove Task-to-Task2 conversion once both are merged.
            tasks = tuple(plug.apply(plugins, Task2.from_task(t)) for t in tasks)

            return Scenario(
                name=to_identifier(
                    path.with_suffix("").name if short_name else str(path)
                ),
                children=tuple(tasks),
                origin=path,
                weight=cls.weight_from_path(path),
            )
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
            raise SkippableScenarioError(path, err)

    @classmethod
    def weight_from_path(cls, path: Path) -> int:
        """
        Reads the weight file corresponding to path, or returns a default weight
        if the weight file doesn't exist.

        :param path: represents either a HAR file or a scenario directory
        :raise WeightValueError: if the weight file exists but its contents cannot be
            interpreted as a weight
        """
        weight_path = path.with_suffix(WEIGHT_FILE_SUFFIX)

        try:
            weight = weight_path.read_text().strip()
        except OSError as err:
            logging.info(
                f"No {weight_path} provided for {path}: "
                f"assigning default weight {DEFAULT_WEIGHT} ({err})"
            )
            return DEFAULT_WEIGHT

        if not weight.isdecimal() or int(weight) == 0:
            logging.error(
                f"invalid weight file %s: weights must be positive integers, got %r",
                weight_path,
                weight,
            )
            raise WeightValueError(path, weight)

        return int(weight)

    @property
    def global_code_blocks(self) -> Mapping[str, Sequence[str]]:
        """
        .. deprecated:: 1.0.2

            This attribute is only kept for backward compatibility purposes.
            It exists because Transformer's first plugin system didn't have
            :term:`OnPythonProgram`, so plugins had to specify the top-level
            locustfile code blocks they needed (e.g. imports, global variables)
            at the :class:`Task` level and let the plugin system percolate these
            code blocks through the scenario tree.
            This explains why tasks have the similar
            :any:`transformer.task.Task2.global_code_blocks` field.
        """
        # TODO: Replace me with a plugin framework that accesses the full tree.
        #   See https://github.com/zalando-incubator/Transformer/issues/11.
        return {
            block_name: block_lines
            for child in self.children
            for block_name, block_lines in child.global_code_blocks.items()
        }

    def apply_plugins(self, plugins: Sequence[Plugin]) -> "Scenario":
        """
        Recursively builds a new scenario tree from the leaves by applying all
        *plugins* to each cloned scenario subtree.

        Does not do anything if *plugins* is empty.

        :param plugins: the plugins to apply.
            See :ref:`Specifying-plugins` for details.
        """
        if not plugins:
            return self

        children = [
            c.apply_plugins(plugins) if isinstance(c, Scenario) else c
            for c in self.children
        ]
        return plug.apply(plugins, dataclasses.replace(self, children=children))
