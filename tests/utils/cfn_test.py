from unittest.mock import Mock, call, patch

import pytest
from botocore.exceptions import ClientError

import cycl.utils.cfn as cfn_module
from cycl.utils.cfn import get_all_exports, get_all_imports, parse_name_from_id


@pytest.fixture
def cfn_client_mock():
    return Mock(name='cfn_client_mock')


@pytest.fixture
def mock_boto3(cfn_client_mock):
    with patch.object(cfn_module, 'boto3') as mock:

        def client_side_effect_func(service, **_kwargs):
            if service == 'cloudformation':
                return cfn_client_mock
            return None

        mock.client.side_effect = client_side_effect_func
        yield mock


@pytest.mark.parametrize(
    ('stack_id', 'expected'),
    [
        ('arn:aws:cloudformation:us-east-1:000000000000:stack/template-1/05a85f80', 'template-1'),
        ('/', ''),
        ('', ''),
    ],
)
def test_parse_name_from_id(stack_id, expected):
    actual = parse_name_from_id(stack_id)
    assert actual == expected


@pytest.mark.parametrize(
    'expected_exports',
    [
        [{'ExportingStackId': 'some-exporting-stack-id', 'Name': 'some-name', 'Value': 'some-value'}],
        [],
    ],
)
def test_get_all_exports_returns_an_export(expected_exports, mock_boto3, cfn_client_mock):
    cfn_client_mock.list_exports.return_value = {'Exports': expected_exports}

    actual_exports = get_all_exports()

    mock_boto3.client.assert_called_once_with('cloudformation')
    assert actual_exports == expected_exports


def test_get_all_exports_conditionally_creates_client(mock_boto3, cfn_client_mock):
    expected_exports = []
    cfn_client_mock.list_exports.return_value = {'Exports': expected_exports}

    actual_exports = get_all_exports(cfn_client=cfn_client_mock)

    mock_boto3.client.assert_not_called()
    assert actual_exports == expected_exports


def test_get_all_exports_uses_next_token(mock_boto3, cfn_client_mock):
    export1 = {'ExportingStackId': 'some-exporting-stack-id-1', 'Name': 'some-name-1', 'Value': 'some-value-1'}
    export2 = {'ExportingStackId': 'some-exporting-stack-id-2', 'Name': 'some-name-2', 'Value': 'some-value-2'}
    expected_exports = [export1, export2]
    cfn_client_mock.list_exports.side_effect = [
        {'Exports': [export1], 'NextToken': 'some-token'},
        {'Exports': [export2]},
    ]

    actual_exports = get_all_exports()

    mock_boto3.client.assert_called_once_with('cloudformation')
    cfn_client_mock.list_exports.assert_has_calls(
        [
            call(),
            call(NextToken='some-token'),
        ],
    )
    assert cfn_client_mock.list_exports.call_count == 2
    assert actual_exports == expected_exports


@pytest.mark.parametrize(
    'expected_imports',
    [
        ['some-import-stack-name'],
        [],
    ],
)
def test_get_all_imports_returns_imports(expected_imports, mock_boto3, cfn_client_mock):
    export_name = 'some-export_name'
    cfn_client_mock.list_imports.return_value = {'Imports': expected_imports}

    actual_imports = get_all_imports(export_name=export_name)

    mock_boto3.client.assert_called_once_with('cloudformation')
    cfn_client_mock.list_imports.assert_called_once_with(ExportName=export_name)
    assert actual_imports == expected_imports


def test_get_all_imports_conditionally_creates_client(mock_boto3, cfn_client_mock):
    export_name = 'some-export_name'
    expected_imports = []
    cfn_client_mock.list_imports.return_value = {'Imports': expected_imports}

    actual_imports = get_all_imports(export_name=export_name, cfn_client=cfn_client_mock)

    mock_boto3.client.assert_not_called()
    assert actual_imports == expected_imports


def test_get_all_imports_uses_next_token(mock_boto3, cfn_client_mock):
    export_name = 'some-export_name'
    import1 = 'some-import-stack-name-1'
    import2 = 'some-import-stack-name-2'
    expected_imports = [import1, import2]
    cfn_client_mock.list_imports.side_effect = [
        {'Imports': [import1], 'NextToken': 'some-token'},
        {'Imports': [import2]},
    ]

    actual_imports = get_all_imports(export_name=export_name)

    mock_boto3.client.assert_called_once_with('cloudformation')
    cfn_client_mock.list_imports.assert_has_calls(
        [
            call(ExportName=export_name),
            call(ExportName=export_name, NextToken='some-token'),
        ],
    )
    assert cfn_client_mock.list_imports.call_count == 2
    assert actual_imports == expected_imports


def test_get_all_imports_excepts_client_error(mock_boto3, cfn_client_mock):
    export_name = 'some-export_name'
    # todo: determine what this error message actually looks like
    cfn_client_mock.list_imports.side_effect = ClientError(
        {'Error': {'Code': 'ValidationError', 'Message': f"Export '{export_name}' is not imported by any stack."}},
        'ListImports',
    )

    actual_imports = get_all_imports(export_name=export_name)

    mock_boto3.client.assert_called_once_with('cloudformation')
    assert actual_imports == []


def test_get_all_imports_raises_client_error(mock_boto3, cfn_client_mock):
    export_name = 'some-export_name'
    cfn_client_mock.list_imports.side_effect = ClientError(
        {'Error': {'Code': 'SomeErrorCode', 'Message': 'is not '}},
        'some_operation',
    )

    with pytest.raises(ClientError):
        get_all_imports(export_name=export_name)

    mock_boto3.client.assert_called_once_with('cloudformation')
