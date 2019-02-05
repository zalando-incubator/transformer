import os
import logging


def on_blacklist(url):
    """
    Checks for matching URLs in an ignore file (blacklist)
    from user's current directory.
    """
    blacklist_file = f"{os.getcwd()}/.urlignore"
    try:
        with open(blacklist_file) as file:
            blacklist = [line.rstrip("\n") for line in file if len(line) > 1]

        for blacklist_item in blacklist:
            if blacklist_item in url:
                return True

        return False

    except OSError as err:
        logging.debug(
            "Could not read blacklist file %s. Reason: %s", blacklist_file, err
        )
        return False
