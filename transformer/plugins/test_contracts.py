import pytest
from hypothesis import given
from hypothesis.strategies import from_type

from transformer.plugins import apply, group_by_contract
from .contracts import (
    Contract,
    plugin,
    contract,
    InvalidContractError,
    InvalidPluginError,
)


@given(from_type(Contract))
def test_contract_returns_contract_associated_with_plugin_decorator(c: Contract):
    @plugin(c)
    def foo():
        ...

    assert contract(foo) is c


def test_plugin_decorator_raises_with_invalid_contract():
    with pytest.raises(InvalidContractError):

        @plugin(2)
        def foo():
            ...


def test_plugin_decorator_raises_without_contract():
    with pytest.raises(InvalidContractError):

        @plugin
        def foo():
            ...


def test_contract_raises_with_invalid_plugin():
    def foo():
        ...

    with pytest.raises(InvalidPluginError):
        contract(foo)


def test_plugin_is_exported_by_the_transformer_plugins_module():
    try:
        from transformer.plugins import plugin
    except ImportError:
        pytest.fail("plugin should be exported by transformer.plugins")


def test_Contract_is_exported_by_the_transformer_plugins_module():
    try:
        from transformer.plugins import Contract
    except ImportError:
        pytest.fail("Contract should be exported by transformer.plugins")


class TestApply:
    def test_return_init_unchanged_without_plugins(self):
        x = object()
        assert apply([], x) is x

    def test_return_plugin_result(self):
        @plugin(Contract.OnTask)
        def plugin_a(x: str) -> str:
            return x + "a"

        assert apply([plugin_a], "z") == "za"

    def test_runs_plugins_in_succession_on_input(self):
        @plugin(Contract.OnTask)
        def plugin_a(x: str) -> str:
            return x + "a"

        @plugin(Contract.OnTask)
        def plugin_b(x: str) -> str:
            return x + "b"

        assert apply((plugin_a, plugin_b), "") == "ab"
        assert apply((plugin_b, plugin_a, plugin_b), "") == "bab"


class TestGroupByContract:
    def test_return_empty_dict_when_no_plugins(self):
        assert group_by_contract([]) == {}

    def test_index_plugins_with_simple_contracts_by_their_contract(self):
        @plugin(Contract.OnTask)
        def plugin_a():
            pass

        @plugin(Contract.OnTask)
        def plugin_b():
            pass

        @plugin(Contract.OnScenario)
        def plugin_z():
            pass

        assert group_by_contract((plugin_a, plugin_b, plugin_z)) == {
            Contract.OnScenario: [plugin_z],
            Contract.OnTask: [plugin_a, plugin_b],
        }

    def test_index_plugins_with_complex_contracts_by_their_basic_contracts(self):
        @plugin(Contract.OnTask)
        def plugin_task():
            pass

        @plugin(Contract.OnTask | Contract.OnScenario | Contract.OnPythonProgram)
        def plugin_multi():
            pass

        assert group_by_contract((plugin_task, plugin_multi)) == {
            Contract.OnTask: [plugin_task, plugin_multi],
            Contract.OnScenario: [plugin_multi],
            Contract.OnPythonProgram: [plugin_multi],
        }
