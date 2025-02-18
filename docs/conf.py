import sys

# import os
from unittest import mock

MOCK_MODULES = ['boto3', 'networkx', 'botocore', 'botocore.config', 'botocore.exceptions']
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()


project = 'cycl'
copyright = '2025, tcm5343'
author = 'tcm5343'
release = '0.2.1'

extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinxarg.ext',
    'sphinx.ext.githubpages',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
