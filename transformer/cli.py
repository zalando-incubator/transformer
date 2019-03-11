"""
Transformer: Convert web browser sessions (HAR files) into Locust load testing
scenarios (locustfiles).

Usage:
    transformer [-p <plugin>]... [<path>...]
    transformer --help
    transformer --version

Options:
    --help              Print this help message and exit.
    -p, --plugin=<name> Use the specified plugin. Repeatable.
    --version           Print version information and exit.

Documentation & code: https://github.com/zalando-incubator/transformer
"""
import logging
import sys
from pathlib import Path
from typing import Sequence, cast, Tuple

import ecological
from docopt import docopt

from transformer import dump
from ._version import __version__


class Config(ecological.AutoConfig, prefix="transformer"):
    input_paths: Tuple[Path, ...] = ()
    plugins: Tuple[str, ...] = ()


def read_config(cli_args: Sequence[str]) -> Config:
    """
    Combine command-line arguments & options (managed by docopt) with environment
    variables (managed by Ecological) into Ecological's Config class.

    Special cases:

    - If input paths are provided both from the environment and the command-line,
      only the paths provided from the command-line are taken into account.
    - If plugins are provided both from the environment and the command-line,
      the union of both groups is taken into account.
    """
    arguments = docopt(__doc__, version=__version__, argv=cli_args)

    # TODO: remove this redundancy once Ecological can re-read the environment
    #  at run-time while still having a compile-time definition (Config).
    #  See https://github.com/jmcs/ecological/issues/20.
    class conf(ecological.AutoConfig, prefix="transformer"):
        input_paths: Tuple[Path, ...] = ()
        plugins: Tuple[str] = ()

    paths = arguments["<path>"]
    if paths:
        if conf.input_paths:
            logging.warning("TRANSFORMER_INPUT_PATHS overwritten with CLI arguments")
        conf.input_paths = paths
    conf.input_paths = tuple(Path(p) for p in conf.input_paths)

    plugins = arguments["--plugin"]
    if plugins:
        if conf.plugins:
            logging.warning("TRANSFORMER_PLUGINS merged with CLI -p/--plugin options")
        conf.plugins = (*conf.plugins, *plugins)

    return cast(Config, conf)


def script_entrypoint() -> None:
    """
    Entrypoint for the "transformer" program (which reads arguments from the
    command-line and the environment).

    This is an alternative to using directly Scenario.from_path and
    locust.locustfile as a library API in another Python program.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s"
    )
    config = read_config(cli_args=sys.argv[1:])
    if not config.input_paths:
        logging.error("No input paths provided in environment nor command-line!")
        logging.info("Did you mean to provide env TRANSFORMER_INPUT_PATHS=[...]?")
        logging.info("Otherwise, here is the command-line manual:")
        print(__doc__, file=sys.stderr)
        exit(1)
    try:
        dump(file=sys.stdout, scenario_paths=config.input_paths, plugins=config.plugins)
    except ImportError as err:
        logging.error(f"Failed loading plugins: {err}")
        exit(2)
    except Exception:
        url = "https://github.com/zalando-incubator/Transformer/issues"
        logging.exception(f"Please help us fix this error by reporting it! {url}")
        exit(3)
