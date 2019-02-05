import logging
import re
import string
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis.strategies import lists, text, recursive, tuples

from transformer.helpers import DUMMY_HAR_STRING, _DUMMY_HAR_DICT
from transformer.scenario import Scenario, SkippableScenarioError, WeightValueError
from transformer.task import Task

paths = recursive(
    text(string.printable.replace("/", ""), min_size=1, max_size=3).filter(
        lambda s: s != "." and s != ".."
    ),
    lambda x: tuples(x, x).map("/".join),
    max_leaves=4,
).map(Path)


class TestScenario:
    @patch("transformer.scenario.Path.is_dir", MagicMock(return_value=False))
    @patch("transformer.scenario.Path.iterdir", MagicMock(return_value=()))
    @patch("transformer.scenario.Path.open")
    @patch("transformer.scenario.json.load", MagicMock(return_value=_DUMMY_HAR_DICT))
    @given(paths=lists(paths, unique=True, min_size=2))
    def test_names_are_unique(*_, paths: List[Path]):
        scenario_names = [Scenario.from_path(path).name for path in paths]
        assert sorted(set(scenario_names)) == sorted(scenario_names)
        assert len(paths) == len(scenario_names)

    def test_creation_from_scenario_directory_with_weight_file(self, tmp_path: Path):
        root_path = tmp_path / "some-path"
        root_path.mkdir()
        expected_weight = 7
        root_path.with_suffix(".weight").write_text(str(expected_weight))
        nb_har_files = 2
        for i in range(nb_har_files):
            root_path.joinpath(f"{i}.har").write_text(DUMMY_HAR_STRING)

        result = Scenario.from_path(root_path)
        assert len(result.children) == nb_har_files
        assert result.weight == expected_weight

    class TestFromPath:
        def test_on_har_raises_error_with_incorrect_har(self, tmp_path: Path):
            not_har_path = tmp_path / "not.har"
            not_har_path.write_text("not JSON!")

            with pytest.raises(SkippableScenarioError):
                Scenario.from_path(not_har_path)

        def test_on_dir_ignores_some_incorrect_hars(self, tmp_path: Path):
            not_har_path = tmp_path / "not.har"
            not_har_path.write_text("not JSON!")
            har_path = tmp_path / "good.har"
            har_path.write_text(DUMMY_HAR_STRING)

            scenario = Scenario.from_path(tmp_path)
            assert len(scenario.children) == 1
            assert scenario.children[0].origin == har_path

        def test_on_dir_raises_error_with_all_incorrect_hars(self, tmp_path: Path):
            for i in range(2):
                tmp_path.joinpath(f"{i}.nothar").write_text("not JSON!")

            with pytest.raises(SkippableScenarioError):
                Scenario.from_path(tmp_path)

        def test_on_dir_with_dangling_weights_raises_error(
            self, tmp_path: Path, caplog
        ):
            (tmp_path / "ok.har").write_text(DUMMY_HAR_STRING)
            (tmp_path / "fail.weight").write_text("7")
            caplog.set_level(logging.INFO)

            with pytest.raises(SkippableScenarioError):
                Scenario.from_path(tmp_path)

            assert "weight file" in caplog.text
            assert any(
                r.levelname == "ERROR" for r in caplog.records
            ), "at least one ERROR logged"

        def test_records_global_code_blocks_from_tasks(self):
            t1_blocks = {"t1-1": ["abc"], "t1-2": ["def"]}
            t1 = Task("t1", request=MagicMock(), global_code_blocks=t1_blocks)
            t2 = Task("t2", request=MagicMock())
            t3_blocks = {"t3-1": ("xyz",)}
            t3 = Task("t3", request=MagicMock(), global_code_blocks=t3_blocks)
            scenario = Scenario("scenario", [t1, t2, t3], origin=None)
            assert scenario.global_code_blocks == {**t1_blocks, **t3_blocks}

        def test_group_records_global_code_blocks_from_scenarios(self):
            t1_blocks = {"t1-1": ["abc"], "t1-2": ["def"]}
            t1 = Task("t1", request=MagicMock(), global_code_blocks=t1_blocks)
            t2 = Task("t2", request=MagicMock())
            t3_blocks = {"t3-1": ("xyz",)}
            t3 = Task("t3", request=MagicMock(), global_code_blocks=t3_blocks)
            s1 = Scenario("s1", [t1, t2], origin=None)
            s2 = Scenario("s2", [t3], origin=None)
            sg = Scenario("sg", [s1, s2], origin=None)
            assert sg.global_code_blocks == {**t1_blocks, **t3_blocks}

        def test_group_records_global_code_blocks_uniquely(self):
            common_blocks = {"x": ["a", "b"]}
            t1 = Task(
                "t1",
                request=MagicMock(),
                global_code_blocks={**common_blocks, "t1b": ["uvw"]},
            )
            t2 = Task(
                "t2",
                request=MagicMock(),
                global_code_blocks={**common_blocks, "t2b": ["xyz"]},
            )
            s1 = Scenario("s1", [t1], origin=None)
            s2 = Scenario("s2", [t2], origin=None)
            sg = Scenario("sg", [s1, s2], origin=None)
            assert sg.global_code_blocks == {
                **common_blocks,
                "t1b": ["uvw"],
                "t2b": ["xyz"],
            }

        def test_without_weight_file_has_weight_1(self, tmp_path: Path):
            har_path = tmp_path / "test.har"
            har_path.write_text(DUMMY_HAR_STRING)
            assert Scenario.from_path(har_path).weight == 1

        def test_with_weight_file_has_corresponding_weight(self, tmp_path: Path):
            weight_path = tmp_path / "test.weight"
            weight_path.write_text("74")

            har_path = tmp_path / "test.har"
            har_path.write_text(DUMMY_HAR_STRING)
            assert Scenario.from_path(har_path).weight == 74

        @pytest.mark.parametrize("weight", [0, -2, 2.1, -2.1, "NaN", "abc", " "])
        def test_with_invalid_weight_raises_error_and_never_skips(
            self, tmp_path: Path, weight
        ):
            legit_har_path = tmp_path / "legit.har"
            legit_har_path.write_text(DUMMY_HAR_STRING)

            bad_weight_path = tmp_path / "test.weight"
            bad_weight_path.write_text(str(weight))

            bad_weight_har_path = tmp_path / "test.har"
            bad_weight_har_path.write_text(DUMMY_HAR_STRING)

            with pytest.raises(WeightValueError):
                # If from_path was skipping the bad scenario/weight pair, it
                # would not raise because there is another valid scenario,
                # legit.har.
                Scenario.from_path(tmp_path)

        def test_with_many_weight_files_selects_weight_based_on_name(
            self, tmp_path: Path
        ):
            expected_weight_path = tmp_path / "test.weight"
            expected_weight_path.write_text("7")

            first_wrong_weight_path = tmp_path / "a.weight"
            first_wrong_weight_path.write_text("2")

            second_wrong_weight_path = tmp_path / "1.weight"
            second_wrong_weight_path.write_text("4")

            har_path = tmp_path / "test.har"
            har_path.write_text(DUMMY_HAR_STRING)

            assert Scenario.from_path(har_path).weight == 7

        def test_uses_full_path_for_scenario_name(self, tmp_path: Path):
            har_basename = "e3ee4a1ef0817cde0a0a78c056e7cb35"
            har_path = tmp_path / har_basename
            har_path.write_text(DUMMY_HAR_STRING)

            scenario = Scenario.from_path(har_path)

            words_in_scenario_name = {
                m.group() for m in re.finditer(r"[A-Za-z0-9]+", scenario.name)
            }
            assert har_basename in words_in_scenario_name

            words_in_parent_path = {
                m.group() for m in re.finditer(r"[A-Za-z0-9]+", str(tmp_path))
            }
            words_in_scenario_name_not_from_har_basename = words_in_scenario_name - {
                har_basename
            }
            assert (
                words_in_parent_path <= words_in_scenario_name_not_from_har_basename
            ), "all components of the parent path must be in the scenario name"

        def test_uses_full_path_for_parents_and_basename_for_children(
            self, tmp_path: Path
        ):
            root_basename = "615010a656a5bb29d1898f163619611f"
            root = tmp_path / root_basename
            root.mkdir()
            for i in range(2):
                (root / f"s{i}.har").write_text(DUMMY_HAR_STRING)

            root_scenario = Scenario.from_path(root)

            words_in_root_scenario_name = {
                m.group() for m in re.finditer(r"[A-Za-z0-9]+", root_scenario.name)
            }
            words_in_root_path = {
                m.group() for m in re.finditer(r"[A-Za-z0-9]+", str(root))
            }
            assert (
                words_in_root_path <= words_in_root_scenario_name
            ), "parent scenario's name must come from full path"

            assert len(root_scenario.children) == 2
            child_scenario_names = {c.name for c in root_scenario.children}
            assert child_scenario_names == {
                "s0",
                "s1",
            }, "child scenarios have short names"

        def test_raises_error_for_colliding_scenario_names_from_har_files(
            self, tmp_path: Path, caplog
        ):
            (tmp_path / "good.har").write_text(DUMMY_HAR_STRING)
            (tmp_path / "bad.har").write_text(DUMMY_HAR_STRING)
            (tmp_path / "bad.json").write_text(DUMMY_HAR_STRING)

            caplog.set_level(logging.ERROR)

            with pytest.raises(SkippableScenarioError):
                Scenario.from_path(tmp_path)

            assert "colliding names" in caplog.text
            assert "bad.har" in caplog.text
            assert "bad.json" in caplog.text

        def test_raises_error_for_colliding_scenario_names_from_directory_and_file(
            self, tmp_path: Path, caplog
        ):
            directory = tmp_path / "x"
            directory.mkdir()
            # directory needs to contain a HAR file, otherwise Transformer will
            # not consider it a scenario.
            (directory / "a.har").write_text(DUMMY_HAR_STRING)

            (tmp_path / "x.har").write_text(DUMMY_HAR_STRING)

            caplog.set_level(logging.ERROR)

            with pytest.raises(SkippableScenarioError):
                Scenario.from_path(tmp_path)

            assert "colliding names" in caplog.text
            assert re.search(r"\bx\b", caplog.text)
            assert re.search(r"\bx.har\b", caplog.text)
