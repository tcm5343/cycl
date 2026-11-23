import logging
from unittest.mock import Mock, patch

import pytest

import cycl._fetch as fetch_module
from cycl import Export, Stack, fetch_exports


def _stack(name, account='000'):
    return Stack(name=name, id=f'arn:{account}:{name}')


def _export(name, exporter, importers=(), account='000'):
    return Export(
        name=name,
        value=f'{name}-value',
        exporting_stack=_stack(exporter, account),
        importing_stacks=tuple(_stack(importer, account) for importer in importers),
    )


def _exports(*exports):
    return {export.name: export for export in exports}


@pytest.fixture(autouse=True)
def mock_boto3():
    with patch.object(fetch_module, 'boto3') as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_list_exports():
    with patch.object(fetch_module, 'list_exports', autospec=True) as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_describe_stacks():
    with patch.object(fetch_module, 'describe_all_stacks', autospec=True) as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture(autouse=True)
def mock_list_importing_stacks():
    with patch.object(fetch_module, 'list_importing_stacks', autospec=True) as mock:
        mock.return_value = []
        yield mock


def test_fetch_exports_returns_empty_exports():
    assert fetch_exports() == {}


def test_fetch_exports_creates_client_with_retry_config(mock_boto3, mock_list_exports):
    fetch_exports()

    mock_boto3.client.assert_called_once()
    assert mock_boto3.client.call_args.args == ('cloudformation',)
    assert mock_boto3.client.call_args.kwargs['config'].retries == {'max_attempts': 10, 'mode': 'adaptive'}
    mock_list_exports.assert_called_once_with(mock_boto3.client.return_value)


def test_fetch_exports_uses_provided_client(mock_boto3, mock_list_exports, mock_list_importing_stacks):
    cfn_client = Mock(name='cfn_client')
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))

    fetch_exports(cfn_client=cfn_client)

    mock_boto3.client.assert_not_called()
    mock_list_exports.assert_called_once_with(cfn_client)
    mock_list_importing_stacks.assert_called_once_with(cfn_client, 'export-1')


def test_fetch_exports_is_keyword_only():
    with pytest.raises(TypeError):
        fetch_exports(Mock())  # type: ignore[misc]


def test_fetch_exports_adds_importing_stacks(mock_list_exports, mock_list_importing_stacks, mock_describe_stacks):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'), _export('export-2', 'stack-b'))
    mock_list_importing_stacks.side_effect = lambda _client, name: {
        'export-1': [Stack(name='stack-b'), Stack(name='stack-c'), Stack(name='stack-c')],
        'export-2': [Stack(name='stack-c')],
    }[name]

    actual = fetch_exports()

    # stack-b exports, so its ARN is known; stack-c only imports
    assert actual == _exports(
        Export(
            name='export-1',
            value='export-1-value',
            exporting_stack=_stack('stack-a'),
            importing_stacks=(_stack('stack-b'), Stack(name='stack-c')),
        ),
        Export(
            name='export-2',
            value='export-2-value',
            exporting_stack=_stack('stack-b'),
            importing_stacks=(Stack(name='stack-c'),),
        ),
    )
    mock_describe_stacks.assert_not_called()


def test_fetch_exports_describe_stacks_resolves_ids_and_tags(
    mock_boto3, mock_list_exports, mock_list_importing_stacks, mock_describe_stacks
):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))
    mock_list_importing_stacks.return_value = [Stack(name='stack-b')]
    stack_a = Stack(name='stack-a', id='arn:000:stack-a', tags={'github-repo': 'repo-a'})
    stack_b = Stack(name='stack-b', id='arn:000:stack-b', tags={'github-repo': 'repo-b'})
    mock_describe_stacks.return_value = {'stack-a': stack_a, 'stack-b': stack_b}

    export = fetch_exports(describe_stacks=True)['export-1']

    mock_describe_stacks.assert_called_once_with(mock_boto3.client.return_value)
    assert export.exporting_stack.tags == {'github-repo': 'repo-a'}
    assert export.importing_stacks == (stack_b,)
    assert export.importing_stacks[0].tags == {'github-repo': 'repo-b'}


def test_fetch_exports_describe_stacks_keeps_stacks_it_cannot_describe(
    caplog, mock_list_exports, mock_list_importing_stacks
):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))
    mock_list_importing_stacks.return_value = [Stack(name='stack-b')]

    with caplog.at_level(logging.WARNING):
        export = fetch_exports(describe_stacks=True)['export-1']

    assert export.exporting_stack == _stack('stack-a')
    assert export.importing_stacks == (Stack(name='stack-b'),)
    assert 'Unable to describe stack stack-a' in caplog.text
    assert 'Unable to describe stack stack-b' in caplog.text


def test_fetch_exports_warns_when_export_has_no_imports(caplog, mock_list_exports):
    mock_list_exports.return_value = _exports(_export('export-1', 'stack-a'))

    with caplog.at_level(logging.WARNING):
        actual = fetch_exports()

    assert actual == _exports(_export('export-1', 'stack-a'))
    assert 'Export found with no import: export-1 from stack-a' in caplog.text
