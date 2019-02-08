from typing import NamedTuple, Union, Iterable, Optional


class Decision(NamedTuple):
    valid: bool
    reason: str

    def __bool__(self) -> bool:
        return self.valid

    def __eq__(self, o: object) -> bool:
        return isinstance(o, self.__class__) and self.valid == o.valid

    @classmethod
    def yes(cls, reason: str = "ok") -> "Decision":
        return Decision(valid=True, reason=reason)

    @classmethod
    def no(cls, reason: str) -> "Decision":
        return Decision(valid=False, reason=reason)

    @classmethod
    def whether(cls, cond: Union[bool, "Decision"], reason: str) -> "Decision":
        if isinstance(cond, Decision):
            if cond:
                return cond
            return Decision.no(f"{reason}: {cond.reason}")
        return Decision.yes(reason) if cond else Decision.no(reason)

    @classmethod
    def all(cls, decisions: Iterable["Decision"]) -> "Decision":
        for d in decisions:
            if not d:
                return d
        return Decision.yes()

    @classmethod
    def any(
        cls, decisions: Iterable["Decision"], reason: Optional[str] = None
    ) -> "Decision":
        recorded_decisions = []
        nb_bad_cases = 0
        BAD_CASES_THRESHOLD = 5
        for d in decisions:
            if d:
                return Decision.yes(f"{reason}: {d.reason}") if reason else d
            if nb_bad_cases <= BAD_CASES_THRESHOLD:
                recorded_decisions.append(d)
            nb_bad_cases += 1

        if nb_bad_cases <= BAD_CASES_THRESHOLD:
            cases = str([d.reason for d in recorded_decisions])
        else:
            cases = f"{nb_bad_cases} invalid cases"

        msg = f"no valid case: {cases}"
        if reason:
            msg = f"{reason}: {msg}"
        return Decision.no(msg)
