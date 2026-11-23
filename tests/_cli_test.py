import json
import logging
import sys
from unittest.mock import patch

import networkx as nx
import pytest

import cycl._cli as cli_module
from cycl._cli import app


def _graph(edges):
    graph = nx.MultiDiGraph()
    graph.add_edges_from(edges)
    return graph


CYCLIC_EDGES = [(1, 2), (2, 1)]


@pytest.fixture(autouse=True)
def mock_fetch_exports():
    with patch.object(cli_module, 'fetch_exports') as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_build_graph():
    with patch.object(cli_module, 'build_graph') as mock:
        mock.return_value = nx.MultiDiGraph()
        yield mock


@pytest.fixture(autouse=True)
def mock_configure_log():
    with patch.object(cli_module, 'configure_log') as mock:
        yield mock


def _run(*argv):
    sys.argv = ['cycl', *argv]
    with pytest.raises(SystemExit) as err:
        app()
    return err.value.code


def test_app_no_cmd_displays_help(capsys):
    assert _run() == 0
    console_output = capsys.readouterr().out
    assert 'usage: cycl [-h] {check,topo}' in console_output
    assert 'Check circular dependencies between imports and exports.' in console_output


def test_app_unsupported_action(capsys):
    assert _run('something') == 2
    assert "cycl: error: argument cmd: invalid choice: 'something'" in capsys.readouterr().err


def test_app_check_acyclic(capsys):
    assert _run('check') == 0
    assert capsys.readouterr().out == ''


def test_app_check_cyclic(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph(CYCLIC_EDGES)

    assert _run('check') == 3
    assert 'cycle found between nodes: [1, 2]' in capsys.readouterr().out


def test_app_check_cyclic_exit_zero(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph(CYCLIC_EDGES)

    assert _run('check', '--exit-zero') == 0
    assert 'cycle found between nodes: [1, 2]' in capsys.readouterr().out


def test_app_check_json(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph(CYCLIC_EDGES)

    assert _run('check', '--format', 'json') == 3
    assert json.loads(capsys.readouterr().out) == {'cycles': [[1, 2]]}


def test_app_check_json_acyclic(capsys):
    assert _run('check', '--format', 'json') == 0
    assert json.loads(capsys.readouterr().out) == {'cycles': []}


@pytest.mark.parametrize(
    ('arg_value', 'log_level'),
    [
        ('CRITICAL', logging.CRITICAL),
        ('DEBUG', logging.DEBUG),
        ('ERROR', logging.ERROR),
        ('INFO', logging.INFO),
        ('WARNING', logging.WARNING),
    ],
)
@pytest.mark.parametrize('cmd', ['check', 'topo'])
def test_app_acyclic_log_level(mock_configure_log, arg_value, log_level, cmd):
    assert _run(cmd, '--log-level', arg_value) == 0
    mock_configure_log.assert_called_with(log_level)


def test_app_topo_cyclic(caplog, capsys, mock_build_graph):
    caplog.set_level(logging.DEBUG)
    mock_build_graph.return_value = _graph(CYCLIC_EDGES)

    assert _run('topo') == 3
    assert 'graph is cyclic, topological generations can only be computed on an acyclic graph' in caplog.text
    assert 'cycle found between nodes: [1, 2]' in capsys.readouterr().out


def test_app_topo_acyclic(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph([('b', 'a'), ('c', 'a'), ('a', 'd')])

    assert _run('topo') == 0
    assert capsys.readouterr().out == 'b c\na\nd\n'


def test_app_topo_empty(capsys):
    assert _run('topo') == 0
    assert capsys.readouterr().out == ''


def test_app_topo_json(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph([('b', 'a'), ('c', 'a')])

    assert _run('topo', '--format', 'json') == 0
    assert json.loads(capsys.readouterr().out) == {'cycles': [], 'generations': [['b', 'c'], ['a']]}


def test_app_topo_json_cyclic(capsys, mock_build_graph):
    mock_build_graph.return_value = _graph(CYCLIC_EDGES)

    assert _run('topo', '--format', 'json') == 3
    assert json.loads(capsys.readouterr().out) == {'cycles': [[1, 2]], 'generations': None}


@pytest.mark.parametrize('cmd', ['check', 'topo'])
def test_app_passes_args(mock_fetch_exports, mock_build_graph, cmd):
    argv = [cmd, '--ignore-node', 'n1', '--ignore-node', 'n2', '--ignore-edge', 'u', 'v']

    assert _run(*argv) == 0

    mock_fetch_exports.assert_called_once_with()
    mock_build_graph.assert_called_once_with(
        mock_fetch_exports.return_value,
        ignore_nodes=['n1', 'n2'],
        ignore_edges=[('u', 'v')],
    )


@pytest.mark.parametrize('cmd', ['check', 'topo'])
def test_app_defaults(mock_fetch_exports, mock_build_graph, cmd):
    assert _run(cmd) == 0

    mock_fetch_exports.assert_called_once_with()
    mock_build_graph.assert_called_once_with(mock_fetch_exports.return_value, ignore_nodes=[], ignore_edges=[])


@pytest.mark.parametrize('argv', [['check', '--unknown-flag'], ['topo', '--format', 'xml'], ['check', '--ignore-edge', 'u']])
def test_app_subcommand_usage_error_exits_two(capsys, argv):
    assert _run(*argv) == 2
    assert 'error:' in capsys.readouterr().err


def test_app_unexpected_error_is_not_caught(mock_fetch_exports):
    """Unexpected errors propagate, so Python exits 1 with a traceback, never the cycle exit code."""
    mock_fetch_exports.side_effect = RuntimeError('boom')

    sys.argv = ['cycl', 'check']
    with pytest.raises(RuntimeError, match='boom'):
        app()
