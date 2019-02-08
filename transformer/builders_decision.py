from hypothesis.strategies import text, builds, booleans, just

from .decision import Decision

reasons = text(max_size=2)

yes_decisions = builds(Decision, valid=just(True), reason=reasons)
no_decisions = builds(Decision, valid=just(False), reason=reasons)

decisions = builds(Decision, valid=booleans(), reason=reasons)
