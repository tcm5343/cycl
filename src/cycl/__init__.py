from importlib.metadata import PackageNotFoundError, version

from .cycl import build_graph, get_graph_data
from .utils.tag import format_tag_name as __format_tag_name

try:
    __version__ = version('cycl')
except PackageNotFoundError:
    __version__ = 'v?'

print(__version__)
