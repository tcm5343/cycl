# Docs are built with the package and its dependencies installed (`pip install .[doc]`),
# so modules like boto3/networkx are imported for real (required by sphinx-argparse).

from datetime import datetime, timezone
from importlib.metadata import version

project = 'cycl'
author = 'tcm5343'
copyright = f'{datetime.now(tz=timezone.utc).year}, {author}'
release = version('cycl')
version = release

extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinxarg.ext',
    'sphinx.ext.githubpages',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'networkx': ('https://networkx.org/documentation/stable', None),
}
autodoc_typehints = 'description'
