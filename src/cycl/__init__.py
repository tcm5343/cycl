import importlib.metadata

from .cycl import get_dependency_graph

__version__ = importlib.metadata.version(__package__ or __name__)
