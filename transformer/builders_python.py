"""
Hypothesis builders for property-based testing of the transformer.python module.
"""
import re
import string
from typing import Optional

from hypothesis.searchstrategy import SearchStrategy
from hypothesis.strategies import (
    integers,
    text,
    lists,
    builds,
    deferred,
    one_of,
    recursive,
    just,
    none,
    booleans,
    floats,
    tuples,
    dictionaries,
)

from transformer import python as py


# Strategy for indentation levels we want to test with (just "no indentation" or
# "one-level indentation" because "two-level indentation" will likely be the
# same, and we don't want the tests running for too long).
indent_levels = integers(min_value=0, max_value=1)


def ascii_text(min_size: int = 0, max_size: Optional[int] = 5) -> SearchStrategy[str]:
    """
    Strategy for ASCII strings, with a default max_size to avoid wasting time
    generating too much.
    """
    return text(string.printable, min_size=min_size, max_size=max_size)


_ascii_inline = re.sub(r"[\r\n\v\f]", "", string.printable)


def ascii_inline_text(
    min_size: int = 0, max_size: Optional[int] = 5
) -> SearchStrategy[str]:
    """Similar to ascii_text, but does not generate multiline strings."""
    return text(_ascii_inline, min_size=min_size, max_size=max_size)


# Strategy for identifiers, i.e. strings that can be used as symbols (function
# names, etc.) in Python programs.
# Unqualified identifiers cannot contain ".", qualified identifiers can
# (but only between unqualified identifiers, i.e. not at the beginning or end).
unqualified_identifiers = text(string.ascii_letters, min_size=1, max_size=5)
qualified_identifiers = lists(unqualified_identifiers, min_size=2, max_size=3).map(
    ".".join
)
identifiers = unqualified_identifiers | qualified_identifiers

# Strategy for python.Line objects.
lines = builds(py.Line, ascii_inline_text(), indent_levels)

# Strategy for lists of strings to be used as comment text in tests.
comments = lists(ascii_inline_text(), max_size=3)

# Strategy for python.Statement objects. Basically, if you ask for a Statement,
# you get an instance of one of Statement's subclasses.
# All Statement subclasses should be mentioned here.
# We need deferred to break the cyclic dependency between builds() that depend statements.
statements = deferred(
    lambda: one_of(
        opaque_blocks,
        functions,
        decorations,
        classes,
        standalones,
        assignments,
        ifelses,
        imports,
    )
)

_atomic_blocks = text(string.ascii_letters + string.punctuation, min_size=1, max_size=3)
_complex_blocks = recursive(
    _atomic_blocks,
    lambda b: text(string.whitespace, min_size=1, max_size=2).flatmap(
        lambda ws: tuples(b, b).map(ws.join)
    ),
    max_leaves=8,
)
# Strategy for python.OpaqueBlock. We don't want whitespace-only comments
# (should be ignored by the syntax tree, which requires boilerplate in tests)
# so we build the text by joining non-whitespace strings together.
# Since this strategy is the default in the statements strategy, which is widely
# used in tests, it should be as fast as possible.
opaque_blocks = builds(py.OpaqueBlock, block=_complex_blocks, comments=comments)

# Strategy for python.Function objects.
functions = builds(
    py.Function,
    name=unqualified_identifiers,
    params=lists(unqualified_identifiers, max_size=2),
    statements=lists(statements, max_size=2),
    comments=comments,
)

# Strategy for python.Class objects.
classes = builds(
    py.Class,
    name=unqualified_identifiers,
    statements=lists(statements, max_size=2),
    superclasses=lists(identifiers, max_size=2),
    comments=comments,
)

# Strategy for python.Decoration objects.
decorations = builds(
    py.Decoration,
    decorator=identifiers,
    target=one_of(functions, classes),
    comments=comments,
)

# Strategy for python.Expression objects. Basically, if you ask for an Expression,
# you get an instance of one of Expression's subclasses.
# All Expression subclasses should be mentioned here.
# Uses deferred for the same reason as Statement.
expressions = deferred(lambda: one_of(symbols, literals, function_calls, binary_ops))

# Strategy for python.Standalone objects.
standalones = builds(py.Standalone, expr=expressions, comments=comments)

# Strategy for python.FString objects. The first examples are supposed to
# trigger interpolation behavior to show that it doesn't happen with FString.
fstrings = builds(
    py.FString, one_of(just(""), just("{a}"), text(min_size=1, max_size=5))
)

# Strategy for python.Literal objects.
# The recursion doesn't use the set data type because python.Statement and
# python.Expression objects are not hashable (because they are not immutable);
# this is also why we use unqualified_identifiers as dictionary keys.
literals = recursive(
    one_of(none(), booleans(), integers(), floats(), text(max_size=5)).map(py.Literal)
    | fstrings,
    lambda x: one_of(
        lists(x, max_size=2),
        tuples(x),
        dictionaries(unqualified_identifiers, x, max_size=2),
    ).map(py.Literal),
    max_leaves=8,
)

# Strategy for python.Symbol objects.
symbols = builds(py.Symbol, identifiers)

# Strategy for python.FunctionCall objects. The size of argument collections is
# limited for performance reasons and because handling 3 arguments is (hopefully)
# the same as handling 2 arguments.
function_calls = builds(
    py.FunctionCall,
    name=identifiers,
    positional_args=lists(expressions, max_size=2),
    named_args=dictionaries(unqualified_identifiers, expressions, max_size=2),
)

# Strategy for reasonable operator names: "+", "++", "in", etc.
operators = text(string.ascii_letters + string.punctuation, min_size=1, max_size=2)
# Strategy for python.BinaryOp.
binary_ops = builds(py.BinaryOp, lhs=expressions, op=operators, rhs=expressions)

# Strategy for python.Assignment.
assignments = builds(py.Assignment, lhs=identifiers, rhs=expressions, comments=comments)

# Strategy for python.IfElse. The size of Statement sub-lists is limited for
# performance reasons and because handling 3 statements is (hopefully) the same
# as handling 2 statements.
ifelses = builds(
    py.IfElse,
    condition_blocks=lists(
        tuples(expressions, lists(statements, max_size=2)), min_size=1, max_size=3
    ),
    else_block=one_of(none(), lists(statements, max_size=2)),
    comments=comments,
)

# Strategy for python.Import without an alias part.
multi_imports = builds(
    py.Import,
    targets=lists(identifiers, min_size=1, max_size=2),
    source=one_of(none(), identifiers),
)
# Strategy for python.Import with an alias part.
aliased_imports = builds(
    py.Import,
    targets=tuples(identifiers),
    source=one_of(none(), identifiers),
    alias=unqualified_identifiers,
)
# Strategy for python.Import.
imports = multi_imports | aliased_imports
