from importlib.metadata import PackageNotFoundError, version

from .cycl import build_graph, get_graph_data

try:
    __version__ = version('cycl')
except PackageNotFoundError:
    __version__ = 'v?'
