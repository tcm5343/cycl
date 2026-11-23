from importlib.metadata import PackageNotFoundError, version

from cycl._fetch import fetch_exports
from cycl._graph import build_graph, merge_graphs
from cycl.models import Export, Stack

try:
    __version__ = version('cycl')
except PackageNotFoundError:
    __version__ = '0.0.0+unknown'

__all__ = [
    'Export',
    'Stack',
    '__version__',
    'build_graph',
    'fetch_exports',
    'merge_graphs',
]
