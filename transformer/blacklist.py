import logging
import os
from typing import Set

Blacklist = Set[str]


def get_empty() -> Blacklist:
    return set()


def from_file() -> Blacklist:
    blacklist_file = f"{os.getcwd()}/.urlignore"
    try:
        with open(blacklist_file) as file:
            return set(filter(None, [line.rstrip() for line in file]))
    except OSError as err:
        logging.debug(
            "Could not read blacklist file %s. Reason: %s", blacklist_file, err
        )
        return get_empty()


def on_blacklist(blacklist: Blacklist, url: str) -> bool:
    """
    Checks for matching URLs in an ignore file (blacklist)
    from user's current directory.
    """
    for blacklist_item in blacklist:
        if blacklist_item in url:
            return True
    return False
