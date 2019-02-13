import pkg_resources
from .transform import dumps, dump

__version__ = pkg_resources.get_distribution("har-transformer").version

__all__ = ["dumps", "dump"]
