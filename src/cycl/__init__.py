from importlib.metadata import PackageNotFoundError, version

from cycl._core import build_graph, fetch_exports
from cycl.exceptions import CyclError
from cycl.models import Export, Stack

try:
    __version__ = version('cycl')
except PackageNotFoundError:
    __version__ = '0.0.0+unknown'

__all__ = [
    'CyclError',
    'Export',
    'Stack',
    '__version__',
    'build_graph',
    'fetch_exports',
]
