import re

from hypothesis import given, example, assume
from hypothesis.strategies import text, from_regex

from transformer.naming import to_identifier

DIGITS_SUFFIX_RX = re.compile(r"_[0-9]+\Z")


class TestToIdentifier:
    @given(text(min_size=1, max_size=3))
    @example("0")
    def test_its_output_can_always_be_used_as_python_identifier(self, s: str):
        exec(f"{to_identifier(s)} = 2")

    @given(text(), text())
    @example("x y", to_identifier("x y"))
    def test_it_has_no_collisions(self, a: str, b: str):
        assert a == b or to_identifier(a) != to_identifier(b)

    @given(from_regex(re.compile(r"[a-z_][a-z0-9_]*", re.IGNORECASE), fullmatch=True))
    def test_it_does_not_add_suffix_when_not_necessary(self, input: str):
        assume(not DIGITS_SUFFIX_RX.search(input))
        assert to_identifier(input) == input

    def test_it_adds_prefix_to_inputs_starting_with_digit(self):
        assert to_identifier("0").startswith("_")
