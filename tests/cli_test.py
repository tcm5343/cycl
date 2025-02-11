import json
import logging
import sys
from unittest.mock import patch

import networkx as nx
import pytest

import cycl.cli as cli_module
from cycl.cli import app


@pytest.fixture(autouse=True)
def mock_build_build_dependency_graph():
    with patch.object(cli_module, 'build_dependency_graph') as mock:
        mock.return_value = nx.MultiDiGraph()
        yield mock


@pytest.fixture(autouse=True)
def mock_configure_log():
    with patch.object(cli_module, 'configure_log') as mock:
        yield mock


def test_app_no_cmd_displays_help(capsys):
    sys.argv = ['cycl']
    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0
    console_output = capsys.readouterr().out
    assert 'usage: cycl [-h] {check,topo}' in console_output
    assert 'Check for cross-stack import/export circular dependencies.' in console_output


def test_app_unsupported_action(capsys):
    sys.argv = ['cycl', 'something']
    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 2
    console_output = capsys.readouterr().err
    assert "cycl: error: argument cmd: invalid choice: 'something'" in console_output


def test_app_check_acyclic():
    sys.argv = ['cycl', 'check']
    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0


def test_app_check_cyclic(capsys, mock_build_build_dependency_graph):
    graph = nx.MultiDiGraph()
    graph.add_edges_from(
        [
            (1, 2),
            (2, 1),
        ]
    )
    mock_build_build_dependency_graph.return_value = graph
    sys.argv = ['cycl', 'check']

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 1
    console_output = capsys.readouterr().out
    assert 'cycle found between nodes: [1, 2]' in console_output


def test_app_check_cyclic_exit_zero(capsys, mock_build_build_dependency_graph):
    graph = nx.MultiDiGraph()
    graph.add_edges_from(
        [
            (1, 2),
            (2, 1),
        ]
    )
    mock_build_build_dependency_graph.return_value = graph
    sys.argv = ['cycl', 'check', '--exit-zero']

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0
    console_output = capsys.readouterr().out
    assert 'cycle found between nodes: [1, 2]' in console_output


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
    sys.argv = ['cycl', cmd, '--log-level', arg_value]

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0
    mock_configure_log.assert_called_with(log_level)


def test_app_topo_cyclic(capsys, mock_build_build_dependency_graph):
    graph = nx.MultiDiGraph()
    graph.add_edges_from(
        [
            (1, 2),
            (2, 1),
        ]
    )
    mock_build_build_dependency_graph.return_value = graph
    sys.argv = ['cycl', 'topo']

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 1
    console_output = capsys.readouterr().out
    assert 'error: graph is cyclic, topological generations can only be computed on an acyclic graph' in console_output


def test_app_topo_acyclic(capsys, mock_build_build_dependency_graph):
    graph = nx.MultiDiGraph()
    graph.add_edges_from(
        [
            (2, 1),
            (3, 1),
        ]
    )
    mock_build_build_dependency_graph.return_value = graph
    expected_output = json.dumps([[2, 3], [1]], indent=2)
    sys.argv = ['cycl', 'topo']

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0
    console_output = capsys.readouterr().out
    assert expected_output in console_output


def test_app_topo_empty(capsys, mock_build_build_dependency_graph):
    graph = nx.MultiDiGraph()
    mock_build_build_dependency_graph.return_value = graph
    expected_output = json.dumps([], indent=2)
    sys.argv = ['cycl', 'topo']

    with pytest.raises(SystemExit) as err:
        app()

    assert err.value.code == 0
    console_output = capsys.readouterr().out
    assert expected_output in console_output
