from typing import Callable
from unittest.mock import MagicMock

import pytest

from transformer.task import Task2
from .contracts import isvalid, Plugin, OnTask


class TestIsvalid:
    def test_no_if_obj_is_not_a_function_regardless_of_plugin(self):
        class A:
            pass

        assert not isvalid(MagicMock(), A())
        assert not isvalid(MagicMock(), 2)
        assert not isvalid(MagicMock(), "x")

    def test_raises_error_for_unknown_plugin(self):
        def f(_: int) -> int:
            ...

        IntPlugin = Callable[[int], int]
        with pytest.raises(TypeError):
            isvalid(IntPlugin, f)

    def test_no_if_obj_has_no_signature(self):
        def f(task):
            return task

        assert not isvalid(OnTask, f)

    def test_no_if_obj_has_wrong_signature(self):
        def f(b: bool) -> bool:
            return b

        assert not isvalid(OnTask, f)

    def test_yes_if_obj_has_right_signature(self):
        def f(t: Task2) -> Task2:
            return t

        assert isvalid(OnTask, f)

    def test_isvalid_plugin_false_if_false_for_all_plugin_subtypes(self):
        def f(t: bool) -> bool:
            return t

        assert not isvalid(Plugin, f)

    def test_isvalid_plugin_true_if_true_for_a_plugin_subtype(self):
        def f(t: Task2) -> Task2:
            return t

        assert isvalid(Plugin, f)
