from typing import List

import pytest
from hypothesis import given, assume
from hypothesis.strategies import booleans, lists

from .builders_decision import reasons, decisions, yes_decisions, no_decisions
from .decision import Decision


@given(decisions)
def test_bool_relies_on_value_only(d: Decision):
    assert bool(d) == d.valid


@given(decisions, decisions)
def test_equality_relies_on_value_only(a: Decision, b: Decision):
    assert (a == b) == (a.valid == b.valid)


class TestYes:
    def test_is_true(self):
        assert Decision.yes().valid is True

    def test_without_argument_has_dummy_reason(self):
        assert Decision.yes().reason.lower() == "ok"

    @given(reasons)
    def test_with_argument_records_reason(self, r: str):
        assert Decision.yes(r).reason == r


class TestNo:
    @given(reasons)
    def test_is_false_regardless_of_reason(self, r: str):
        assert Decision.no(r).valid is False

    def test_without_argument_raises_error(self):
        with pytest.raises(Exception):
            Decision.no()

    @given(reasons)
    def test_reason_is_recorded_and_accessible(self, r: str):
        assert Decision.no(r).reason == r


class TestWhether:
    @given(decisions, reasons)
    def test_wrapper_propagates_wrapped_value(self, d: Decision, r: str):
        assert Decision.whether(d, r).valid == d.valid

    @given(yes_decisions, reasons)
    def test_reuses_wrapped_reason_when_true(self, y: Decision, r: str):
        assert Decision.whether(y, r).reason == y.reason

    @given(no_decisions, reasons)
    def test_enriches_wrapped_reason_when_false(self, n: Decision, r: str):
        assert Decision.whether(n, r).reason == f"{r}: {n.reason}"

    @given(booleans())
    def test_accepts_raw_bool(self, b: bool):
        d = Decision.whether(b, "x")
        assert d.valid == b
        assert d.reason == "x", "reason is always recorded"


class TestAll:
    @given(lists(booleans()))
    def test_behaves_like_builtin(self, bs: List[bool]):
        bs_as_decisions = (Decision(valid=b, reason="") for b in bs)
        assert all(bs) == bool(Decision.all(bs_as_decisions))

    def test_reuse_first_wrapped_no_reason(self):
        y = Decision.yes()
        n1 = Decision.no("n1")
        n2 = Decision.no("n2")
        assert Decision.all((y, n1, y, n2, y)) == n1


class TestAny:
    @given(lists(booleans()))
    def test_behaves_like_builtin(self, bs: List[bool]):
        bs_as_decisions = (Decision(valid=b, reason="") for b in bs)
        assert any(bs) == bool(Decision.any(bs_as_decisions))

    def test_reuse_first_wrapped_yes_reason(self):
        y1 = Decision.yes("y1")
        y2 = Decision.yes("y2")
        n = Decision.no("n")
        assert Decision.any((n, y1, n, y2, n)) == y1

    @given(lists(no_decisions, max_size=5))
    def test_reason_lists_invalid_cases_if_5_or_less(self, ds: List[Decision]):
        d = Decision.any(ds)
        assert str([x.reason for x in ds]) in d.reason

    def test_reason_mentions_number_of_invalid_cases_if_more_than_5(self):
        nb_cases = 10
        ds = [Decision.no("X") for _ in range(nb_cases)]
        d = Decision.any(ds)
        assert str(nb_cases) in d.reason

    @given(decisions, reasons)
    def test_provided_reason_prefixes_default_message(self, d: Decision, r: str):
        assume(r)
        assert Decision.any([d], r).reason == f"{r}: {Decision.any([d]).reason}"
