import re
import zlib

DIGIT_RX = re.compile(r"[0-9]")
ENDS_WITH_ADLER32 = re.compile(r"_[0-9]+\Z")


def to_identifier(string: str) -> str:
    """
    Replace everything except letters, digits and underscore with underscores,
    allowing the resulting name to be used as identifier in a Python program.

    A checksum is added at the end (to avoid collisions) if at least one
    replacement is made, or if the input already ends like a checksum
    (otherwise, for any input X, we have:
        to_identifier(X) == to_identifier(to_identifier(X))
    i.e. a collision).
    """
    safe_name = re.sub(r"[^_a-z0-9]", "_", string, flags=re.IGNORECASE)
    if DIGIT_RX.match(safe_name):
        safe_name = f"_{safe_name}"
    if safe_name == string and not ENDS_WITH_ADLER32.search(string):
        return string
    unique_suffix: int = zlib.adler32(string.encode())
    return f"{safe_name}_{unique_suffix}"
