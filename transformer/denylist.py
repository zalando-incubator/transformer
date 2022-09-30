import warnings
import logging
import os
from typing import Set
import re

Denylist = Set[str]


def get_empty() -> Denylist:
    return set()


def from_file() -> Denylist:
    if os.path.exists(f"{os.getcwd()}/.urlignore"):
        warnings.warn(
            "Legacy .urlignore file detected - it will not be used! Rename it to '.ignore' if you want to use it, and read about the difference in the documentation."
        )
    denylist_file = f"{os.getcwd()}/.ignore"
    try:
        with open(denylist_file, encoding="utf-8") as file:
            return set(filter(None, [line.rstrip() for line in file]))
    except OSError as err:
        logging.debug("Could not read denylist file %s. Reason: %s", denylist_file, err)
        return get_empty()


def on_denylist(denylist: Denylist, url: str) -> bool:
    """
    Checks for matching URLs in an ignore file (denylist)
    from user's current directory.
    """
    for denylist_item in denylist:
        if re.search(denylist_item, url):
            return True
    return False
