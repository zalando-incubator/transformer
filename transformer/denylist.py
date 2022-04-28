import logging
import os
from typing import Set

Denylist = Set[str]


def get_empty() -> Denylist:
    return set()


def from_file() -> Denylist:
    denylist_file = f"{os.getcwd()}/.urlignore"
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
        if denylist_item in url:
            return True
    return False
