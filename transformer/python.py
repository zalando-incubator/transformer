"""
:mod:`transformer.python` -- Python Syntax Tree
===============================================

Transformer's Python Syntax Tree framework allows you to create and manipulate
Python source code without bothering with irrelevant, style-related details.

It is the main API for writing :term:`OnPythonProgram` plugins.

A non-goal of this framework is *customization of style*: users should rely on
an external tool (such as `black`_) if they need style customization of their
generated locustfile.

.. _black: https://github.com/ambv/black
"""

import re
from types import MappingProxyType
from typing import (
    Sequence,
    Mapping,
    Any,
    List,
    Type,
    Set,
    Optional,
    Tuple,
    cast,
    Iterable,
    Callable,
    TypeVar,
    ClassVar,
)

from dataclasses import dataclass

IMMUTABLE_EMPTY_DICT = MappingProxyType({})


@dataclass
class Line:
    """
    A line of text and its associated indentation level.

    This class allows not to constantly copy strings to add a new indentation
    level at every scope of the syntax tree.

    .. attribute:: text

       :any:`str` -- Text contained by this line.

    .. attribute:: indent_level

       :any:`int` -- Indentation level of :attr:`text` in the line.
    """

    text: str
    indent_level: int = 0

    INDENT_UNIT: ClassVar[str] = " " * 4

    def __str__(self) -> str:
        """
        Textual representation of this line, with :attr:`text` indented
        according to :attr:`indent_level`.
        """
        return f"{self.INDENT_UNIT * self.indent_level}{self.text}"

    def clone(self) -> "Line":
        """
        Creates an exact but disconnected copy of self.
        Useful in tests.
        """
        return type(self)(text=self.text, indent_level=self.indent_level)


def _resplit(parts: Iterable[str]) -> List[str]:
    """
    Given a list of strings, returns a list of lines, by splitting each string
    into multiple lines where it contains newlines.

    >>> _resplit([])
    []
    >>> _resplit(['a', 'b'])
    ['a', 'b']
    >>> _resplit(['a', 'b\\nc\\nd'])
    ['a', 'b', 'c', 'd']
    """
    return [line for part in parts for line in part.splitlines()]


class Statement:
    """
    Python distinguishes between statements and expressions: basically,
    statements cannot be assigned to a variable, whereas expressions can.

    For our purpose, another distinction is important: statements may span over
    multiple lines (and not just for style), whereas all expressions can be
    expressed in a single line.

    This class serves as abstract base for all implementors of :meth:`lines` and
    handles comment processing for them.
    """

    def __init__(self, comments: Sequence[str] = ()) -> None:
        """
        :param comments: Comment lines attached to this statement.
        """
        self._comments = _resplit(comments)

    @property
    def comments(self) -> List[str]:
        """
        Comment lines attached to this statement.

        This is a :class:`property` to ensure that modifications of this list
        preserve the invariant "one element = one line".
        """
        self._comments = _resplit(self._comments)
        return self._comments

    @comments.setter
    def comments(self, value: List[str]):
        self._comments = value

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        """
        All Line objects necessary to represent this Statement, along with the
        appropriate indentation level.

        :param indent_level: How much indentation to apply to the least indented
            line of this statement.
        :param comments: Whether existing comments attached to *self* should be
            included in the result.
        """
        raise NotImplementedError

    def comment_lines(self, indent_level: int) -> List[Line]:
        """
        Converts self.comments from str to Line with ``#`` prefixes.
        """
        return [Line(f"# {s}", indent_level) for s in self.comments]

    def attach_comment(self, line: Line) -> List[Line]:
        """
        Attach a comment to *line*: inline if *self.comments* is just one line,
        on dedicated new lines above otherwise.
        """
        comments = self.comments
        if not comments:
            return [line]
        if len(comments) == 1:
            line.text += f"  # {comments[0]}"
            return [line]
        lines = self.comment_lines(line.indent_level)
        lines.append(line)
        return lines

    def __eq__(self, o: object) -> bool:
        return (
            isinstance(o, self.__class__)
            and self.comments == cast(__class__, o).comments
        )


# Handy alias for type signatures.
Program = Sequence[Statement]


class OpaqueBlock(Statement):
    """
    A block of code already represented as a string.
    This helps moving existing code (e.g. in plugins) from our ad-hoc
    "blocks of code" framework to the syntax tree framework defined in this
    module.
    It also allows to express Python constructs that would otherwise not yet be
    representable with this AST framework.
    """

    PREFIX_RX = re.compile(r"\s+")
    TAB_SIZE = 8

    def __init__(self, block: str, comments: Sequence[str] = ()) -> None:
        """
        :param block: String representing a block of Python code.
        """
        super().__init__(comments)
        if not block.strip():
            raise ValueError(f"OpaqueBlock can't be empty but got {block!r}")
        self.block = block

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        raw_lines = [l.expandtabs(self.TAB_SIZE) for l in self.block.splitlines()]

        first_nonempty_line = next(i for i, l in enumerate(raw_lines) if l.strip())
        after_last_nonempty_line = next(
            len(raw_lines) - i for i, l in enumerate(reversed(raw_lines)) if l.strip()
        )
        raw_lines = raw_lines[first_nonempty_line:after_last_nonempty_line]

        indents = [self.PREFIX_RX.match(l) for l in raw_lines]
        shortest_indent = min(len(p.group()) if p else 0 for p in indents)
        block_lines = [Line(l[shortest_indent:], indent_level) for l in raw_lines]
        if comments:
            return [*self.comment_lines(indent_level), *block_lines]
        return block_lines

    def __repr__(self) -> str:
        return "{}({!r}, comments={!r})".format(
            self.__class__.__qualname__, self.block, self.comments
        )

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o) and self.block == cast(__class__, o).block


class Function(Statement):
    """
    A function definition (``def ...``).
    """

    def __init__(
        self,
        name: str,
        params: Sequence[str],
        statements: Sequence[Statement],
        comments: Sequence[str] = (),
    ) -> None:
        """
        :param name: Name of this function.
        :param params: Names of each parameter of this function.
        :param statements: Body of this function.
        """
        super().__init__(comments)
        self.name = name
        self.params = list(params)
        self.statements = list(statements)

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        param_list = ", ".join(self.params)
        body_lines = [
            line
            for stmt in self.statements
            for line in stmt.lines(indent_level + 1, comments)
        ] or [Line("pass", indent_level + 1)]
        top = Line(f"def {self.name}({param_list}):", indent_level)
        if comments:
            return [*self.attach_comment(top), *body_lines]
        return [top, *body_lines]

    def __repr__(self) -> str:
        return "{}(name={!r}, params={!r}, statements={!r}, comments={!r})".format(
            self.__class__.__qualname__,
            self.name,
            self.params,
            self.statements,
            self.comments,
        )

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.name == cast(__class__, o).name
            and self.params == cast(__class__, o).params
            and self.statements == cast(__class__, o).statements
        )


class Decoration(Statement):
    """
    A function or class definition to which is applied a decorator
    (e.g. ``@task``).
    """

    def __init__(
        self, decorator: str, target: Statement, comments: Sequence[str] = ()
    ) -> None:
        """
        :param decorator: Name of the decorator applied to *target*.
        :param target: Function or class definition to which is applied
            *decorator*.
        """
        super().__init__(comments)
        self.decorator = decorator
        self.target = target

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        top = Line(f"@{self.decorator}", indent_level)
        target_lines = self.target.lines(indent_level, comments)
        if comments:
            return [*self.attach_comment(top), *target_lines]
        return [top, *target_lines]

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, comments={!r})".format(
            self.__class__.__qualname__, self.decorator, self.target, self.comments
        )

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.decorator == cast(__class__, o).decorator
            and self.target == cast(__class__, o).target
        )


class Class(Statement):
    """
    A class definition.
    """

    def __init__(
        self,
        name: str,
        statements: Sequence[Statement],
        superclasses: Sequence[str] = (),
        comments: Sequence[str] = (),
    ) -> None:
        """
        :param name: Name of this class.
        :param statements: Fields of this class: methods, attributes, etc.
        :param superclasses: Names of each superclass of this class.
            In fact anything in the "function argument" format can be used here,
            like keyword-arguments (but in a string!).
        """
        super().__init__(comments)
        self.name = name
        self.statements = list(statements)
        self.superclasses = list(superclasses)

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        superclasses = ""
        if self.superclasses:
            superclasses = "({})".format(", ".join(self.superclasses))

        body = [
            line
            for stmt in self.statements
            for line in stmt.lines(indent_level + 1, comments)
        ] or [Line("pass", indent_level + 1)]

        top = Line(f"class {self.name}{superclasses}:", indent_level)
        if comments:
            return [*self.attach_comment(top), *body]
        return [top, *body]

    def __repr__(self) -> str:
        return (
            "{}(name={!r}, statements={!r}, " "superclasses={!r}, comments={!r})"
        ).format(
            self.__class__.__qualname__,
            self.name,
            self.statements,
            self.superclasses,
            self.comments,
        )

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.name == cast(__class__, o).name
            and self.statements == cast(__class__, o).statements
            and self.superclasses == cast(__class__, o).superclasses
        )


class Expression:
    """
    See the documentation of :class:`Statement` for why Expression is a separate
    class.
    An expression is still a statement in Python (e.g. functions can be called
    anywhere), but this :class:`Expression` class is **not** a
    :class:`Statement` because we can't attach comments to arbitrary expressions
    (e.g. between braces).
    If you need to use an :class:`Expression` as a :class:`Statement`,
    see the :class:`Standalone` wrapper class.

    This class serves as abstract base for all our implementors of
    :meth:`__str__`.
    """

    def __str__(self) -> str:
        raise NotImplementedError

    def __eq__(self, o: object) -> bool:
        return isinstance(o, self.__class__)


class Standalone(Statement):
    """
    Wraps an :class:`Expression` so that it can be used as a :class:`Statement`.
    """

    def __init__(self, expr: Expression, comments: Sequence[str] = ()) -> None:
        """
        :param expr: The wrapped expression.
        """
        super().__init__(comments)
        self.expr = expr

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        """
        An :class:`Expression` E used as a :class:`Statement` is serialized as
        the result of :samp:`str({E})` on its own :class:`Line`.
        """
        line = Line(str(self.expr), indent_level)
        if comments:
            return self.attach_comment(line)
        return [line]

    def __repr__(self) -> str:
        return "{}({!r}, comments={!r})".format(
            self.__class__.__qualname__, self.expr, self.comments
        )

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o) and self.expr == cast(__class__, o).expr


def _all_subclasses_of(cls: Type) -> Set[Type]:
    """
    All subclasses of *cls*, including non-direct ones (child of child of ...).
    """
    direct_subclasses = set(cls.__subclasses__())
    return direct_subclasses.union(
        s for d in direct_subclasses for s in _all_subclasses_of(d)
    )


class Literal(Expression):
    """
    All literal Python expressions (integers, strings, lists, etc.).

    Everything will be serialized using :func:`repr`, except :class:`Expression`
    objects that could be contained in a composite value like ``list``:
    they will be serialized with :func:`str`, as is probably expected.
    Thus:

    >>> str(Literal([1, {"a": FString("-{x}")}]))
    "[1, {'a': f'-{x}'}]"

    instead of something like ``[1, {'a': FString('-{x}')}]``.

    .. seealso:: :class:`FString`
    """

    def __init__(self, value: Any) -> None:
        """
        :param value: The Python literal represented by this node.
        """
        super().__init__()
        self.value = value

    _REPR_BY_EXPR_CLS = None

    def __str__(self) -> str:
        # This is not pretty, but repr() doesn't accept a visitor we could use
        # to say "just this time, use that code to serialize Expression objects".
        if Literal._REPR_BY_EXPR_CLS is None:
            Literal._REPR_BY_EXPR_CLS = {
                c: c.__repr__ for c in _all_subclasses_of(Expression)
            }
        try:
            for k in Literal._REPR_BY_EXPR_CLS.keys():
                k.__repr__ = k.__str__
            return repr(self.value)
        finally:
            for k, _repr in Literal._REPR_BY_EXPR_CLS.items():
                k.__repr__ = _repr

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.value!r})"

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o) and self.value == cast(__class__, o).value


class FString(Literal):
    """
    f-strings_ are strings that capture values from their environment.

    They cannot be handled in :class:`Literal` because they are a "trick" of the
    Python parser: *before* the program runs, they lose their ``f`` prefix and
    their template is evaluated, so when :class:`Literal` is instantiated, they
    are only a normal string that tried to capture values from Transformer's
    context (instead of *the locustfile's* context).

    .. _f-strings: https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep498
    """

    def __init__(self, s: str) -> None:
        """
        :param s: The template of this f-string,
            for example ``a{x}b`` for the f-string ``f"a{x}b"``.
        """
        if not isinstance(s, str):
            raise TypeError(
                f"expecting a format string, got {s.__class__.__qualname__}: {s!r}"
            )
        super().__init__(s)

    def __str__(self) -> str:
        return "f" + repr(str(self.value))


class Symbol(Expression):
    """
    The name of something (variable, function, etc.).
    Avoids any kind of string quoting and escaping that would happen with
    :class:`Literal`.

    >>> str(Literal("x"))
    "'x'"
    >>> str(Symbol("x"))
    'x'

    The provided argument's type is explicitly checked and a :class:`TypeError`
    may be raised to avoid confusion when a user expects e.g. ``Symbol(True)``
    to work like ``Symbol("True")``.
    """

    def __init__(self, name: str) -> None:
        """
        :param name: Textual representation of this symbol.
            Will be forwarded without modification to the locustfile.
        """
        super().__init__()
        if not isinstance(name, str):
            raise TypeError(
                f"expected symbol name, got {name.__class__.__qualname__}: {name!r}"
            )
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.name!r})"

    def __eq__(self, o: object) -> bool:
        return super().__eq__(o) and self.name == cast(__class__, o).name


class FunctionCall(Expression):
    """
    The invocation of a function or method.
    """

    def __init__(
        self,
        name: str,
        positional_args: Sequence[Expression] = (),
        named_args: Mapping[str, Expression] = IMMUTABLE_EMPTY_DICT,
    ) -> None:
        """
        :param name: Name of the function that is called.
        :param positional_args: Positional arguments associated with this call,
            if any.
        :param named_args: Keyword-arguments associated with this call, if any.
        """
        super().__init__()
        self.name = name
        self.positional_args = list(positional_args)
        self.named_args = dict(named_args)

    def __str__(self) -> str:
        args = [str(a) for a in self.positional_args] + [
            f"{k}={v}" for k, v in self.named_args.items()
        ]
        return f"{self.name}({', '.join(args)})"

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, {!r})".format(
            self.__class__.__qualname__,
            self.name,
            self.positional_args,
            self.named_args,
        )

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.name == cast(__class__, o).name
            and self.positional_args == cast(__class__, o).positional_args
            and self.named_args == cast(__class__, o).named_args
        )


class BinaryOp(Expression):
    """
    The invocation of a binary operator.

    To avoid any precedence error in the generated code, operands that are also
    BinaryOps are always surrounded by braces (even when not necessary, as in
    "1 + (2 + 3)", as a more subtle behavior would increase the complexity of
    the implementation without much benefit.
    """

    def __init__(self, lhs: Expression, op: str, rhs: Expression) -> None:
        """
        :param lhs: Left-hand side operand of this operation.
        :param op: Name of the operator, like ``+``.
        :param rhs: Right-hand side operand of this operation.
        """
        super().__init__()
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __str__(self) -> str:
        operands = [self.lhs, self.rhs]
        return f" {self.op} ".join(
            f"({x})" if isinstance(x, BinaryOp) else str(x) for x in operands
        )

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.lhs == cast(__class__, o).lhs
            and self.op == cast(__class__, o).op
            and self.rhs == cast(__class__, o).rhs
        )


class Assignment(Statement):
    """
    The assignment of a value to a variable.

    For our purposes, we don't treat multiple assignment via tuples differently.
    We also don't support chained assignments such as ``a = b = 1``.
    """

    def __init__(self, lhs: str, rhs: Expression, comments: Sequence[str] = ()) -> None:
        """
        :param lhs: Variable name (or names) the *rhs* is assigned to.
        :param rhs: Expression which value is assigned to *lhs*.
        """
        super().__init__(comments)
        self.lhs = lhs
        self.rhs = rhs

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        line = Line(f"{self.lhs} = {self.rhs}", indent_level)
        if comments:
            return self.attach_comment(line)
        return [line]

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.lhs == cast(__class__, o).lhs
            and self.rhs == cast(__class__, o).rhs
        )

    def __repr__(self) -> str:
        return "{}(lhs={!r}, rhs={!r}, comments={!r})".format(
            self.__class__.__qualname__, self.lhs, self.rhs, self.comments
        )


class IfElse(Statement):
    """
    The if/elif/else construct, where elif and else are optional and elif can
    be repeated.
    """

    def __init__(
        self,
        condition_blocks: Sequence[Tuple[Expression, Sequence[Statement]]],
        else_block: Optional[Sequence[Statement]] = None,
        comments: Sequence[str] = (),
    ) -> None:
        """
        :param condition_blocks: Pairs of condition and statements.
            Each pair is composed of an expression representing a condition,
            and a list of statements corresponding to that condition.
            This represents an if/elif/.../elif sequence, where there is always
            an "if" clause and an arbitrary number of "elif" clauses.
        :param else_block: Statements representing the "else" clause, if any.
        :raise ValueError: If there is not at least one element in
            *condition_blocks*.
        """
        super().__init__(comments)
        self.condition_blocks = [
            (cond, list(stmts)) for cond, stmts in condition_blocks
        ]
        self._assert_consistency()
        self.else_block = else_block

    def _assert_consistency(self):
        if not self.condition_blocks:
            raise ValueError("can't have an if without at least one block")

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        self._assert_consistency()
        lines = []
        for i, block in enumerate(self.condition_blocks):
            keyword = "if" if i == 0 else "elif"
            lines.append(Line(f"{keyword} {block[0]}:", indent_level))
            lines.extend(
                [
                    line
                    for stmt in block[1]
                    for line in stmt.lines(indent_level + 1, comments)
                ]
                or [Line("pass", indent_level + 1)]
            )
        if self.else_block:
            lines.append(Line("else:", indent_level))
            lines.extend(
                [
                    line
                    for stmt in self.else_block
                    for line in stmt.lines(indent_level + 1, comments)
                ]
            )
        if comments:
            # There is always a first line, or _assert_consistency would fail.
            return [*self.attach_comment(lines[0]), *lines[1:]]
        return lines

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.condition_blocks == cast(__class__, o).condition_blocks
            and self.else_block == cast(__class__, o).else_block
        )

    def __repr__(self) -> str:
        return "{}(condition_blocks={!r}, else_block={!r}, comments={!r})".format(
            self.__class__.__qualname__,
            self.condition_blocks,
            self.else_block,
            self.comments,
        )


class Import(Statement):
    """
    The import statement in all its forms: ``import X``, ``import X as A``,
    ``from M import X``, ``from M import X as A``, and ``from M import X, Y``.

    Combined imports like ``from M import X, Y`` are split for simplicity.
    """

    def __init__(
        self,
        targets: Sequence[str],
        source: Optional[str] = None,
        alias: Optional[str] = None,
        comments: Sequence[str] = (),
    ) -> None:
        """
        :param targets: What is imported: *X* in :samp:`import {X}` and
            :samp:`from M import {X}`.
        :param source: From where *targets* are imported, if applicable: *M* in
            :samp:`from {M} import X`.
        :param alias: Alias for a single-element *targets*: *A* in
            :samp:`import X as {A}` and :samp:`from M import X as {A}`.
        :raise ValueError: If *targets* is empty, or if *alias* is specified
            even though there are multiple *targets*.
        """
        super().__init__(comments)
        self.targets = list(targets)
        self.source = source
        self.alias = alias
        self._assert_consistency()

    def _assert_consistency(self):
        if not self.targets:
            raise ValueError("expected at least one import target")
        if len(self.targets) > 1 and self.alias:
            raise ValueError("alias forbidden for multiple import targets")

    def lines(self, indent_level: int = 0, comments: bool = True) -> List[Line]:
        self._assert_consistency()
        import_kw = f"from {self.source} import" if self.source else "import"
        alias_clause = f" as {self.alias}" if self.alias else ""
        lines = [
            Line(f"{import_kw} {target}{alias_clause}", indent_level)
            for target in self.targets
        ]
        if comments:
            return [*self.comment_lines(indent_level), *lines]
        return lines

    def __eq__(self, o: object) -> bool:
        return (
            super().__eq__(o)
            and self.targets == cast(__class__, o).targets
            and self.source == cast(__class__, o).source
            and self.alias == cast(__class__, o).alias
        )

    def __repr__(self) -> str:
        return "{}(targets={!r}, source={!r}, alias={!r}, comments={!r})".format(
            self.__class__.__qualname__,
            self.targets,
            self.source,
            self.alias,
            self.comments,
        )


_T = TypeVar("_T")


@dataclass
class ExpressionView(Expression):
    """
    A "proxy" for an object that is not an :class:`Expression`.

    .. |Expr| replace:: :class:`Expression`
    .. |EV| replace:: :class:`ExpressionView`

    |EV| allows to mix non-|Expr| objects in the syntax tree, along with
    a function capable of transforming these objects into actual |Expr| objects
    at any time.
    This is useful when these objects are easier to manipulate than their |Expr|
    equivalent.

    .. |Request| replace:: :class:`Request <transformer.request.Request>`

    For example: any |Request| object can be converted into an equivalent |Expr|,
    but |Request| has a simpler API than |Expr| for request-oriented operations
    like accessing the URL, etc.
    |EV| can "wrap" a |Request| to pretend that the |Request| is an |Expr|
    (with all associated benefits of being part of the syntax tree), but still
    support the |Request| API.

    .. attribute:: target

        :any:`() → T <typing.Callable>` --
        A function (without parameters) returning the wrapped, non-|Expr| object.

        The benefit of :attr:`target` being a function (instead of a direct
        reference to the wrapped object) is that it allows to specify some
        mutable field of an object.
        See for example :class:`Task2 <transformer.task.Task2>`, which contains
        an |EV| wrapping its own :attr:`request <transformer.task.Task2.request>`
        attribute.
        If the value of that attribute changes, the |EV| will refer to the new
        value (found by accessing the attribute via *self*),
        not the old value (which would still be referenced by a non-callable
        :attr:`target`).

    .. attribute:: converter

        :any:`T → <typing.Callable>` |Expr| --
        A function capable of transforming the result of :attr:`target` into
        an |Expr|.
        The result of :attr:`converter` is computed each time this |EV| has to
        behave like an |Expr|, for example when passed as argument to :any:`str`.

    .. attribute:: name

        :any:`str` --
        Purely descriptive: makes the inspection of data structures containing
        |EV| objects more comfortable.
    """

    target: Callable[[], _T]
    converter: Callable[[_T], Expression]
    name: str

    def __str__(self) -> str:
        return str(self.converter(self.target()))
