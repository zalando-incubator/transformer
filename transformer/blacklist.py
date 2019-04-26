import os
import logging
from typing import Sequence

Blacklist = Sequence[str]


def from_file() -> Blacklist:
    blacklist_file = f"{os.getcwd()}/.urlignore"
    try:
        with open(blacklist_file) as file:
            return [line.rstrip("\n") for line in file if len(line) > 1]
    except OSError as err:
        logging.debug(
            "Could not read blacklist file %s. Reason: %s", blacklist_file, err
        )


def on_blacklist(blacklist: Blacklist, url: str) -> bool:
    """
    Checks for matching URLs in an ignore file (blacklist)
    from user's current directory.
    """
    if blacklist:
        for blacklist_item in blacklist:
            if blacklist_item in url:
                return True
    return False
